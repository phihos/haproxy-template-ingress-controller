"""
Application state models for HAProxy Template IC.

This module defines strongly-typed state models to replace the dynamic kopf.Memo
object, eliminating defensive programming patterns throughout the codebase.
"""

import asyncio
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, SecretStr, field_serializer, field_validator

# Import all types that will be used in model fields
try:
    from kopf._core.engines.indexing import OperatorIndices
except ImportError:
    # Fallback for when kopf is not available during testing or development
    OperatorIndices = Any

from haproxy_template_ic.activity import ActivityBuffer, get_activity_buffer
from haproxy_template_ic.credentials import Credentials, DataplaneAuth
from haproxy_template_ic.dataplane.synchronizer import ConfigSynchronizer
from haproxy_template_ic.debouncer import TemplateRenderDebouncer
from haproxy_template_ic.metrics import MetricsCollector, get_metrics_collector
from haproxy_template_ic.templating import TemplateRenderer

from .config import Config, PodSelector, TemplateConfig
from .context import HAProxyConfigContext, TemplateContext


class RuntimeState(BaseModel):
    """Runtime control and task management state."""

    stop_flag: asyncio.Future[None]
    config_reload_flag: asyncio.Future[None]
    cli_options: Any = Field(..., description="CLI options object from Click")
    socket_server_task: Optional[asyncio.Task] = Field(default=None)

    model_config = {"arbitrary_types_allowed": True}

    @field_serializer("stop_flag", "config_reload_flag")
    def serialize_future(self, future: asyncio.Future[None]) -> bool:
        """Serialize Future as boolean indicating if it's done."""
        return future.done()

    @field_validator("stop_flag", "config_reload_flag", mode="before")
    @classmethod
    def deserialize_future(cls, v: Any) -> asyncio.Future[None]:
        """Deserialize boolean back to Future."""
        if isinstance(v, bool):
            future: asyncio.Future[None] = asyncio.Future()
            if v:  # If the flag was set
                future.set_result(None)
            return future
        return v  # Already a Future

    @field_serializer("socket_server_task")
    def serialize_task(self, task: Optional[asyncio.Task]) -> Optional[bool]:
        """Serialize task as boolean indicating if it exists and is not done."""
        return task is not None and not task.done() if task else None

    @field_serializer("cli_options")
    def serialize_cli_options(self, cli_options: Any) -> Dict[str, Any]:
        """Extract serializable fields from CLI options."""
        return {
            "configmap_name": getattr(cli_options, "configmap_name", None),
            "secret_name": getattr(cli_options, "secret_name", None),
            "webhook_enabled": getattr(cli_options, "webhook_enabled", False),
            "verbose": getattr(cli_options, "verbose", 0),
        }


class ConfigurationState(BaseModel):
    """Configuration and template rendering state."""

    config: Config
    haproxy_config_context: HAProxyConfigContext
    credentials: Credentials = Field(
        ..., description="Always loaded before operator starts"
    )
    template_renderer: TemplateRenderer = Field(
        ..., description="Always created from config"
    )

    model_config = {"arbitrary_types_allowed": True}

    @field_serializer("config")
    def serialize_config(self, config: Config) -> Dict[str, Any]:
        """Serialize Config using Pydantic model_dump."""
        return config.model_dump(mode="json")

    @field_serializer("haproxy_config_context")
    def serialize_haproxy_config_context(
        self, context: HAProxyConfigContext
    ) -> Dict[str, Any]:
        """Serialize HAProxyConfigContext using Pydantic model_dump."""
        return context.model_dump(mode="json")

    @field_serializer("credentials")
    def serialize_credentials(self, credentials: Credentials) -> Dict[str, Any]:
        """Serialize Credentials using Pydantic model_dump."""
        return credentials.model_dump(mode="json")

    @field_serializer("template_renderer")
    def serialize_template_renderer(self, renderer: TemplateRenderer) -> str:
        """Serialize TemplateRenderer as string representation."""
        return f"<TemplateRenderer: {len(getattr(renderer, '_template_files', {}))} template files>"


class ResourceState(BaseModel):
    """Kubernetes resource indexing and metadata state."""

    indices: OperatorIndices = Field(..., description="kopf resource indices")
    resource_metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    @field_serializer("indices")
    def serialize_indices(self, indices: OperatorIndices) -> Dict[str, Any]:
        """Serialize OperatorIndices with basic metadata."""
        if hasattr(indices, "__dict__"):
            # Try to get basic info about the indices
            info = {"type": str(type(indices).__name__), "available": True}
            # Try to get some safe metadata if available
            if hasattr(indices, "_storage") and hasattr(indices._storage, "__len__"):
                info["storage_count"] = len(indices._storage)
            return info
        return {"type": "OperatorIndices", "available": bool(indices)}


class OperationalState(BaseModel):
    """Operational services and monitoring state."""

    activity_buffer: ActivityBuffer = Field(
        ..., description="Always initialized before operator starts"
    )
    debouncer: TemplateRenderDebouncer = Field(
        ..., description="Always created in startup hook"
    )
    metrics: MetricsCollector = Field(..., description="Always created in startup hook")
    config_synchronizer: ConfigSynchronizer = Field(
        ..., description="Always initialized with empty production URLs"
    )

    model_config = {"arbitrary_types_allowed": True}

    @field_serializer("activity_buffer")
    def serialize_activity_buffer(self, buffer: ActivityBuffer) -> Dict[str, Any]:
        """Serialize ActivityBuffer with basic info."""
        return {"type": str(type(buffer).__name__), "active": True}

    @field_serializer("debouncer")
    def serialize_debouncer(self, debouncer: TemplateRenderDebouncer) -> Dict[str, Any]:
        """Serialize TemplateRenderDebouncer with configuration."""
        return {
            "type": "TemplateRenderDebouncer",
            "min_interval": getattr(debouncer, "min_interval", 0),
            "max_interval": getattr(debouncer, "max_interval", 0),
            "active": True,
        }

    @field_serializer("metrics")
    def serialize_metrics(self, metrics: MetricsCollector) -> Dict[str, Any]:
        """Serialize MetricsCollector with basic info."""
        return {"type": "MetricsCollector", "active": True}

    @field_serializer("config_synchronizer")
    def serialize_config_synchronizer(
        self, synchronizer: ConfigSynchronizer
    ) -> Dict[str, Any]:
        """Serialize ConfigSynchronizer with basic info."""
        return {
            "type": "ConfigSynchronizer",
            "production_urls": getattr(synchronizer, "production_urls", []),
            "validation_url": getattr(synchronizer, "validation_url", ""),
            "active": True,
        }


class ApplicationState(BaseModel):
    """
    Complete application state replacing kopf.Memo.

    This strongly-typed state object eliminates the need for defensive programming
    by making all attributes explicit with proper types and Optional annotations
    where attributes may not be initialized.
    """

    runtime: RuntimeState
    configuration: ConfigurationState
    resources: ResourceState
    operations: OperationalState

    model_config = {"arbitrary_types_allowed": True}

    @property
    def config(self) -> Config:
        """Direct access to configuration for backwards compatibility."""
        return self.configuration.config

    @property
    def haproxy_config_context(self) -> HAProxyConfigContext:
        """Direct access to HAProxy config context for backwards compatibility."""
        return self.configuration.haproxy_config_context

    @property
    def indices(self) -> OperatorIndices:
        """Direct access to resource indices for backwards compatibility."""
        return self.resources.indices

    @property
    def credentials(self) -> Credentials:
        """Direct access to credentials for backwards compatibility."""
        return self.configuration.credentials

    @property
    def template_renderer(self) -> TemplateRenderer:
        """Direct access to template renderer for backwards compatibility."""
        return self.configuration.template_renderer

    @property
    def activity_buffer(self) -> ActivityBuffer:
        """Direct access to activity buffer for backwards compatibility."""
        return self.operations.activity_buffer

    @property
    def debouncer(self) -> TemplateRenderDebouncer:
        """Direct access to debouncer for backwards compatibility."""
        return self.operations.debouncer

    @property
    def metrics(self) -> MetricsCollector:
        """Direct access to metrics collector for backwards compatibility."""
        return self.operations.metrics

    @property
    def config_synchronizer(self) -> ConfigSynchronizer:
        """Direct access to config synchronizer for backwards compatibility."""
        return self.operations.config_synchronizer

    @property
    def cli_options(self) -> Any:
        """Direct access to CLI options for backwards compatibility."""
        return self.runtime.cli_options

    @property
    def stop_flag(self) -> asyncio.Future[None]:
        """Direct access to stop flag for backwards compatibility."""
        return self.runtime.stop_flag

    @property
    def config_reload_flag(self) -> asyncio.Future[None]:
        """Direct access to config reload flag for backwards compatibility."""
        return self.runtime.config_reload_flag

    @property
    def socket_server_task(self) -> Optional[asyncio.Task]:
        """Direct access to socket server task for backwards compatibility."""
        return self.runtime.socket_server_task

    @property
    def resource_metadata(self) -> Dict[str, Any]:
        """Direct access to resource metadata for backwards compatibility."""
        return self.resources.resource_metadata

    def has_resource_indices(self) -> bool:
        """Check if resource indices are available and not empty."""
        return bool(self.resources.indices)

    def has_socket_server_task(self) -> bool:
        """Check if socket server task is running."""
        return (
            self.runtime.socket_server_task is not None
            and not self.runtime.socket_server_task.done()
        )

    def get_namespace(self) -> str:
        """Get the effective namespace from various sources."""
        # Check HAProxy config context first
        if hasattr(
            self.configuration.haproxy_config_context.template_context, "namespace"
        ):
            namespace = (
                self.configuration.haproxy_config_context.template_context.namespace
            )
            if namespace:
                return namespace

        # Check config namespace
        if hasattr(self.configuration.config, "namespace"):
            namespace = getattr(self.configuration.config, "namespace", None)
            if namespace:
                return namespace

        # Check CLI options
        if hasattr(self.runtime.cli_options, "namespace"):
            namespace = getattr(self.runtime.cli_options, "namespace", None)
            if namespace:
                return namespace

        # Default fallback
        return "default"

    @classmethod
    def create_with_initial_values(
        cls,
        stop_flag: asyncio.Future[None],
        config_reload_flag: asyncio.Future[None],
        cli_options: Any,
        indices: OperatorIndices,
        config: Optional[Config] = None,
        credentials: Optional[Credentials] = None,
        template_renderer: Optional[TemplateRenderer] = None,
        production_urls: Optional[List[str]] = None,
        url_to_pod_name: Optional[Dict[str, str]] = None,
    ) -> "ApplicationState":
        """
        Create ApplicationState with configuration values.

        If config/credentials are provided, use them. Otherwise create placeholders.
        """

        if config is None:
            # Create minimal placeholder config
            config = Config(
                pod_selector=PodSelector(match_labels={"app": "haproxy"}),
                haproxy_config=TemplateConfig(template="# Initial config"),
            )

        if template_renderer is None:
            # Create template renderer from config
            template_renderer = TemplateRenderer.from_config(config)

        if credentials is None:
            # Create placeholder credentials
            credentials = Credentials(
                dataplane=DataplaneAuth(username="admin", password=SecretStr("temp")),
                validation=DataplaneAuth(username="admin", password=SecretStr("temp")),
            )

        # Create initial config synchronizer with discovered production URLs
        # Import ConfigSynchronizer locally to avoid circular imports
        initial_config_synchronizer = ConfigSynchronizer(
            production_urls=production_urls or [],
            validation_url="http://localhost:5555",
            credentials=credentials,
            activity_buffer=get_activity_buffer(),
            url_to_pod_name=url_to_pod_name or {},
        )

        return cls(
            runtime=RuntimeState(
                stop_flag=stop_flag,
                config_reload_flag=config_reload_flag,
                cli_options=cli_options,
            ),
            configuration=ConfigurationState(
                config=config,
                haproxy_config_context=HAProxyConfigContext(
                    template_context=TemplateContext(namespace="default"),
                    rendered_config=None,
                ),
                credentials=credentials,
                template_renderer=template_renderer,
            ),
            resources=ResourceState(
                indices=indices,
            ),
            operations=OperationalState(
                activity_buffer=get_activity_buffer(),
                debouncer=TemplateRenderDebouncer(
                    min_interval=5,
                    max_interval=60,
                    render_func=lambda memo, force=False: asyncio.sleep(
                        0
                    ),  # Placeholder async function
                    memo=None,  # Will be set later
                ),
                metrics=get_metrics_collector(),
                config_synchronizer=initial_config_synchronizer,
            ),
        )

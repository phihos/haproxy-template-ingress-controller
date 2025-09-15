"""
Application state models for HAProxy Template IC.

This module defines strongly-typed state models to replace the dynamic kopf.Memo
object, eliminating defensive programming patterns throughout the codebase.
"""

import asyncio
from typing import Optional

from kopf._core.engines.indexing import OperatorIndices
from pydantic import BaseModel, Field

from haproxy_template_ic.credentials import Credentials
from haproxy_template_ic.dataplane.synchronizer import ConfigSynchronizer
from haproxy_template_ic.debouncer import TemplateRenderDebouncer
from haproxy_template_ic.metrics import MetricsCollector
from haproxy_template_ic.templating import TemplateRenderer

from .config import Config
from .context import HAProxyConfigContext

from .cli import CliOptions


class RuntimeState(BaseModel):
    """Runtime control and task management state."""

    stop_flag: asyncio.Future[None]
    config_reload_flag: asyncio.Future[None]
    cli_options: CliOptions = Field(..., description="CLI options object from Click")
    socket_server_task: Optional[asyncio.Task] = Field(default=None)

    model_config = {"arbitrary_types_allowed": True}


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


class ResourceState(BaseModel):
    """Kubernetes resource indexing and metadata state."""

    indices: OperatorIndices = Field(..., description="kopf resource indices")

    model_config = {"arbitrary_types_allowed": True}


class OperationalState(BaseModel):
    """Operational services and monitoring state."""

    debouncer: TemplateRenderDebouncer = Field(
        ..., description="Always created in startup hook"
    )
    metrics: MetricsCollector = Field(..., description="Always created in startup hook")
    config_synchronizer: ConfigSynchronizer = Field(
        ..., description="Always initialized with empty production URLs"
    )

    model_config = {"arbitrary_types_allowed": True}


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
    def debouncer(self) -> TemplateRenderDebouncer:
        """Direct access to debouncer for backwards compatibility."""
        return self.operations.debouncer

    @property
    def metrics(self) -> MetricsCollector:
        """Direct access to metrics collector for backwards compatibility."""
        return self.operations.metrics

    @property
    def config_synchronizer(self) -> "ConfigSynchronizer":
        """Direct access to config synchronizer for backwards compatibility."""
        return self.operations.config_synchronizer

    @property
    def cli_options(self) -> "CliOptions":
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

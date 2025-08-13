from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from pathlib import Path

from jinja2 import Template, TemplateSyntaxError


class WatchResourceCollection(list):
    """Collection of WatchResourceConfig objects with convenient lookup methods."""

    def by_id(self, resource_id: str) -> Optional["WatchResourceConfig"]:
        """Find a watch resource by its id."""
        for resource in self:
            if resource.id == resource_id:
                return resource
        return None


class MapCollection(list):
    """Collection of MapConfig objects with convenient lookup methods."""

    def by_path(self, path: str) -> Optional["MapConfig"]:
        """Find a map by its path."""
        for map_config in self:
            if map_config.path == path:
                return map_config
        return None


class TemplateSnippetCollection(list):
    """Collection of TemplateSnippet objects with convenient lookup methods."""

    def by_name(self, name: str) -> Optional["TemplateSnippet"]:
        """Find a template snippet by its name."""
        for snippet in self:
            if snippet.name == name:
                return snippet
        return None


class CertificateCollection(list):
    """Collection of CertificateConfig objects with convenient lookup methods."""

    def by_name(self, name: str) -> Optional["CertificateConfig"]:
        """Find a certificate by its name."""
        for cert in self:
            if cert.name == name:
                return cert
        return None


def config_from_dict(config_dict: Dict[str, Any]) -> "Config":
    """Convert dictionary configuration to Config object."""

    def make_template(template_str: str) -> Template:
        """Convert string to Jinja2 template with validation."""
        try:
            return Template(template_str)
        except TemplateSyntaxError as e:
            raise ValueError(f"Invalid template: {e}")

    def parse_pod_selector(data: Any) -> PodSelector:
        """Parse pod_selector field."""
        if not isinstance(data, dict):
            raise ValueError(f"pod_selector must be a dict, got {type(data)}")
        match_labels = data.get("match_labels", {})
        if not isinstance(match_labels, dict):
            raise ValueError("pod_selector.match_labels must be a dict")
        return PodSelector(match_labels=match_labels)

    def parse_resource_filter(data: Dict[str, Any]) -> Optional[ResourceFilter]:
        """Parse optional resource filter."""
        if not data:
            return None
        return ResourceFilter(
            namespace_selector=data.get("namespace_selector"),
            field_selector=data.get("field_selector"),
            label_selector=data.get("label_selector"),
        )

    def parse_watch_resources(data: Any) -> WatchResourceCollection:
        """Parse watch_resources from dict or list."""
        if not data:
            return WatchResourceCollection()

        items = []
        if isinstance(data, dict):
            # Convert dict format: {id: {kind: ..., ...}}
            for resource_id, config in data.items():
                if not isinstance(config, dict):
                    raise ValueError(f"Watch resource '{resource_id}' must be a dict")
                if "kind" not in config:
                    raise ValueError(
                        f"Watch resource '{resource_id}' missing required 'kind'"
                    )

                items.append(
                    WatchResourceConfig(
                        id=resource_id,
                        kind=config["kind"],
                        group=config.get("group"),
                        version=config.get("version"),
                        filter=parse_resource_filter(config.get("filter", {})),
                    )
                )
        elif isinstance(data, list):
            # List format: [{id: ..., kind: ..., ...}, ...]
            for config in data:
                if not isinstance(config, dict):
                    raise ValueError("Watch resource must be a dict")
                if "kind" not in config:
                    raise ValueError("Watch resource missing required 'kind'")

                items.append(
                    WatchResourceConfig(
                        id=config.get("id", ""),
                        kind=config["kind"],
                        group=config.get("group"),
                        version=config.get("version"),
                        filter=parse_resource_filter(config.get("filter", {})),
                    )
                )
        else:
            raise ValueError("watch_resources must be a dict or list")

        return WatchResourceCollection(items)

    def parse_maps(data: Any) -> MapCollection:
        """Parse maps from dict or list."""
        if not data:
            return MapCollection()

        items = []
        if isinstance(data, dict):
            # Convert dict format: {path: {template: ...}}
            for path, config in data.items():
                if not Path(path).is_absolute():
                    raise ValueError(f"Map path '{path}' must be absolute")
                if not isinstance(config, dict):
                    raise ValueError(f"Map config for '{path}' must be a dict")
                if "template" not in config:
                    raise ValueError(f"Map '{path}' missing required 'template'")

                items.append(
                    MapConfig(
                        path=path,
                        template=make_template(config["template"]),
                    )
                )
        elif isinstance(data, list):
            # List format: [{path: ..., template: ...}, ...]
            for config in data:
                if not isinstance(config, dict):
                    raise ValueError("Map config must be a dict")
                if "path" not in config:
                    raise ValueError("Map missing required 'path'")
                if "template" not in config:
                    raise ValueError("Map missing required 'template'")

                path = config["path"]
                if not Path(path).is_absolute():
                    raise ValueError(f"Map path '{path}' must be absolute")

                items.append(
                    MapConfig(
                        path=path,
                        template=make_template(config["template"]),
                    )
                )
        else:
            raise ValueError("maps must be a dict or list")

        return MapCollection(items)

    def parse_template_snippets(data: Any) -> TemplateSnippetCollection:
        """Parse template_snippets from dict or list."""
        if not data:
            return TemplateSnippetCollection()

        items = []
        if isinstance(data, dict):
            # Convert dict format: {name: {template: ...}}
            for name, config in data.items():
                if not isinstance(config, dict):
                    raise ValueError(f"Template snippet '{name}' must be a dict")
                if "template" not in config:
                    raise ValueError(
                        f"Template snippet '{name}' missing required 'template'"
                    )

                items.append(
                    TemplateSnippet(
                        name=name,
                        template=make_template(config["template"]),
                    )
                )
        elif isinstance(data, list):
            # List format: [{name: ..., template: ...}, ...]
            for config in data:
                if not isinstance(config, dict):
                    raise ValueError("Template snippet must be a dict")
                if "name" not in config:
                    raise ValueError("Template snippet missing required 'name'")
                if "template" not in config:
                    raise ValueError("Template snippet missing required 'template'")

                items.append(
                    TemplateSnippet(
                        name=config["name"],
                        template=make_template(config["template"]),
                    )
                )
        else:
            raise ValueError("template_snippets must be a dict or list")

        return TemplateSnippetCollection(items)

    def parse_certificates(data: Any) -> CertificateCollection:
        """Parse certificates from dict or list."""
        if not data:
            return CertificateCollection()

        items = []
        if isinstance(data, dict):
            # Convert dict format: {name: {template: ...}}
            for name, config in data.items():
                if not isinstance(config, dict):
                    raise ValueError(f"Certificate '{name}' must be a dict")
                if "template" not in config:
                    raise ValueError(
                        f"Certificate '{name}' missing required 'template'"
                    )

                items.append(
                    CertificateConfig(
                        name=name,
                        template=make_template(config["template"]),
                    )
                )
        elif isinstance(data, list):
            # List format: [{name: ..., template: ...}, ...]
            for config in data:
                if not isinstance(config, dict):
                    raise ValueError("Certificate must be a dict")
                if "name" not in config:
                    raise ValueError("Certificate missing required 'name'")
                if "template" not in config:
                    raise ValueError("Certificate missing required 'template'")

                items.append(
                    CertificateConfig(
                        name=config["name"],
                        template=make_template(config["template"]),
                    )
                )
        else:
            raise ValueError("certificates must be a dict or list")

        return CertificateCollection(items)

    # Validate input
    if not isinstance(config_dict, dict):
        raise ValueError("Configuration must be a dictionary")

    # Parse required fields
    if "pod_selector" not in config_dict:
        raise ValueError("Missing required field: pod_selector")
    if "haproxy_config" not in config_dict:
        raise ValueError("Missing required field: haproxy_config")

    pod_selector = parse_pod_selector(config_dict["pod_selector"])
    haproxy_config = make_template(config_dict["haproxy_config"])

    # Parse optional collections
    watch_resources = parse_watch_resources(config_dict.get("watch_resources"))
    maps = parse_maps(config_dict.get("maps"))
    template_snippets = parse_template_snippets(config_dict.get("template_snippets"))
    certificates = parse_certificates(config_dict.get("certificates"))

    return Config(
        pod_selector=pod_selector,
        haproxy_config=haproxy_config,
        watch_resources=watch_resources,
        template_snippets=template_snippets,
        maps=maps,
        certificates=certificates,
    )


@dataclass(frozen=True)
class ResourceFilter:
    namespace_selector: Optional[Dict[str, Any]] = None
    field_selector: Optional[Dict[str, str]] = None
    label_selector: Optional[Dict[str, str]] = None


@dataclass(frozen=True)
class WatchResourceConfig:
    kind: str
    id: str = ""
    group: Optional[str] = None
    version: Optional[str] = None
    filter: Optional[ResourceFilter] = None


@dataclass(frozen=True)
class MapConfig:
    template: Template
    path: str = ""


@dataclass(frozen=True)
class TemplateSnippet:
    template: Template
    name: str = ""


@dataclass(frozen=True)
class CertificateConfig:
    template: Template
    name: str = ""


@dataclass(frozen=True)
class PodSelector:
    match_labels: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Config:
    pod_selector: PodSelector
    haproxy_config: Template
    watch_resources: WatchResourceCollection = field(
        default_factory=WatchResourceCollection
    )
    template_snippets: TemplateSnippetCollection = field(
        default_factory=TemplateSnippetCollection
    )
    maps: MapCollection = field(default_factory=MapCollection)
    certificates: CertificateCollection = field(default_factory=CertificateCollection)


@dataclass(frozen=True)
class RenderedMap:
    path: str
    content: str
    map_config: "MapConfig"


@dataclass(frozen=True)
class TemplateContext:
    resources: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    cluster_name: str = "default"
    config_values: Dict[str, Any] = field(default_factory=dict)
    config: Optional["Config"] = None

    def register_error(self, resource_key: str, resource_id: str, error: str) -> None:
        pass

    def get_template_snippet(self, name: str) -> Optional["TemplateSnippet"]:
        """Get a template snippet by name for use in templates."""
        if self.config:
            return self.config.template_snippets.by_name(name)
        return None

    def get_map_config(self, path: str) -> Optional["MapConfig"]:
        """Get a map config by path for use in templates."""
        if self.config:
            return self.config.maps.by_path(path)
        return None

    def get_certificate_config(self, name: str) -> Optional["CertificateConfig"]:
        """Get a certificate config by name for use in templates."""
        if self.config:
            return self.config.certificates.by_name(name)
        return None


@dataclass
class HAProxyConfigContext:
    rendered_maps: List[RenderedMap] = field(default_factory=list)

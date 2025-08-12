from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from pathlib import Path

from dacite import from_dict, Config as DaciteConfig
from jinja2 import Template, TemplateSyntaxError


def config_from_dict(config_dict):
    # Custom type hook to compile Jinja2 templates
    def compile_template(template_str: str) -> Template:
        try:
            return Template(template_str)
        except TemplateSyntaxError as e:
            raise ValueError(f"Invalid Jinja2 template: {e}")

    config = from_dict(
        Config,
        config_dict,
        config=DaciteConfig(strict=True, type_hooks={Template: compile_template}),
    )

    # Validate that all map keys are absolute paths
    for map_key in config.maps.keys():
        if not Path(map_key).is_absolute():
            raise ValueError(f"Map key '{map_key}' must be an absolute path")

    return config


@dataclass(frozen=True)
class WatchResourceConfig:
    kind: str
    group: Optional[str] = None
    version: Optional[str] = None


@dataclass(frozen=True)
class MapConfig:
    path: str
    template: Template


@dataclass(frozen=True)
class Config:
    pod_selector: str
    watch_resources: Dict[str, WatchResourceConfig] = field(default_factory=dict)
    maps: Dict[str, MapConfig] = field(default_factory=dict)


@dataclass(frozen=True)
class RenderedMap:
    """Represents a rendered HAProxy map file."""

    path: str
    content: str
    map_config: "MapConfig"


@dataclass(frozen=True)
class TemplateContext:
    """Template context data for rendering HAProxy configuration."""

    resources: Dict[str, Any] = field(default_factory=dict)
    # Example of future field that will be automatically available in templates
    cluster_name: str = "default"


@dataclass
class HAProxyConfigContext:
    """Container for all rendered HAProxy configuration files."""

    rendered_maps: Dict[str, RenderedMap] = field(default_factory=dict)

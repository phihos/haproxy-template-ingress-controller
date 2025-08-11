from dataclasses import dataclass, field
from typing import Dict, Optional

from dacite import from_dict


def config_from_dict(config_dict):
    return from_dict(Config, config_dict)


@dataclass(frozen=True)
class WatchResourceConfig:
    group: Optional[str] = None
    version: Optional[str] = None
    kind: Optional[str] = None


@dataclass(frozen=True)
class MapConfig:
    path: str
    template: str


@dataclass(frozen=True)
class Config:
    pod_selector: str
    watch_resources: Dict[str, WatchResourceConfig] = field(default_factory=dict)
    maps: Dict[str, MapConfig] = field(default_factory=dict)

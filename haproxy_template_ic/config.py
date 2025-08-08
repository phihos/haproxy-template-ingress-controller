from dataclasses import dataclass, field
from typing import Dict
from dacite import from_dict


def config_from_dict(config_dict):
    return from_dict(Config, config_dict)


@dataclass(frozen=True)
class MapConfig:
    path: str
    template: str


@dataclass(frozen=True)
class Config:
    pod_selector: str
    maps: Dict[str, str] = field(default_factory=dict)

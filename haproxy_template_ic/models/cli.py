from dataclasses import dataclass


@dataclass(frozen=True)
class CliOptions:
    """Container for bootstrap CLI options (configmap and secret location)."""

    configmap_name: str
    secret_name: str

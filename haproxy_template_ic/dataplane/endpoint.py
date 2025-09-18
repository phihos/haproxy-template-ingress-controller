"""
Dataplane endpoint models for clean URL/pod bundling.

This module provides immutable dataclasses that bundle dataplane URLs with
their associated pod names, eliminating parameter proliferation and providing
rich context for error reporting and logging.
"""

from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

from haproxy_template_ic.credentials import DataplaneAuth
from .utils import normalize_dataplane_url, extract_hostname_from_url


@dataclass(frozen=True)
class DataplaneEndpoint:
    """Immutable bundle of dataplane URL with authentication and associated pod name."""

    url: str
    dataplane_auth: DataplaneAuth
    pod_name: Optional[str] = None

    def __post_init__(self):
        """Validate and normalize URL on creation."""
        if not self.url:
            raise ValueError("URL cannot be empty")

        # Basic URL validation
        try:
            parsed = urlparse(self.url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL format: {self.url}")
        except Exception as e:
            raise ValueError(f"Invalid URL format: {self.url}") from e

        # Normalize URL and store it
        normalized = normalize_dataplane_url(self.url)
        object.__setattr__(self, "url", normalized)

    @property
    def hostname(self) -> str:
        """Extract hostname from URL for display/logging."""
        return extract_hostname_from_url(self.url) or "unknown"

    @property
    def display_name(self) -> str:
        """Human-readable name for logging/UI."""
        return self.pod_name or self.hostname

    def __str__(self) -> str:
        """String representation for logging with pod context."""
        if self.pod_name:
            return f"{self.url} (pod: {self.pod_name})"
        return self.url

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        if self.pod_name:
            return f"DataplaneEndpoint(url='{self.url}', auth_user='{self.dataplane_auth.username}', pod_name='{self.pod_name}')"
        return f"DataplaneEndpoint(url='{self.url}', auth_user='{self.dataplane_auth.username}')"


@dataclass(frozen=True)
class DataplaneEndpointSet:
    """Immutable collection of dataplane endpoints with validation."""

    validation: DataplaneEndpoint
    production: List[DataplaneEndpoint]

    def __post_init__(self):
        """Validate endpoint set consistency."""
        # Note: Empty production endpoints are allowed during initialization
        # since pods are discovered dynamically at runtime
        pass

        # Check for URL duplicates across all endpoints
        all_urls = [self.validation.url] + [ep.url for ep in self.production]
        if len(set(all_urls)) != len(all_urls):
            duplicate_urls = [url for url in all_urls if all_urls.count(url) > 1]
            raise ValueError(f"Duplicate URLs in endpoint set: {duplicate_urls}")

        # Check for pod name duplicates (if specified)
        pod_names = [ep.pod_name for ep in self.all_endpoints() if ep.pod_name]
        if pod_names and len(set(pod_names)) != len(pod_names):
            duplicate_pods = [name for name in pod_names if pod_names.count(name) > 1]
            raise ValueError(f"Duplicate pod names in endpoint set: {duplicate_pods}")

    def all_endpoints(self) -> List[DataplaneEndpoint]:
        """Get all endpoints (validation + production)."""
        return [self.validation] + self.production

    def find_by_pod_name(self, pod_name: str) -> Optional[DataplaneEndpoint]:
        """Find endpoint by pod name."""
        for endpoint in self.all_endpoints():
            if endpoint.pod_name == pod_name:
                return endpoint
        return None

    def find_by_url(self, url: str) -> Optional[DataplaneEndpoint]:
        """Find endpoint by URL (with normalization)."""
        try:
            normalized_url = normalize_dataplane_url(url)
            for endpoint in self.all_endpoints():
                if endpoint.url == normalized_url:
                    return endpoint
        except Exception:
            # If URL normalization fails, try direct comparison
            for endpoint in self.all_endpoints():
                if endpoint.url == url:
                    return endpoint
        return None

    def find_by_hostname(self, hostname: str) -> List[DataplaneEndpoint]:
        """Find endpoints by hostname (may return multiple)."""
        matches = []
        for endpoint in self.all_endpoints():
            if endpoint.hostname == hostname:
                matches.append(endpoint)
        return matches

    def get_production_by_index(self, index: int) -> Optional[DataplaneEndpoint]:
        """Get production endpoint by index (safe access)."""
        if 0 <= index < len(self.production):
            return self.production[index]
        return None

    def __len__(self) -> int:
        """Total number of endpoints (validation + production)."""
        return len(self.all_endpoints())

    def __iter__(self):
        """Iterate over all endpoints."""
        return iter(self.all_endpoints())

    def __str__(self) -> str:
        """String representation for logging."""
        prod_count = len(self.production)
        prod_text = f"{prod_count} production endpoint{'s' if prod_count != 1 else ''}"
        return f"validation={self.validation}, {prod_text}"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"DataplaneEndpointSet("
            f"validation={repr(self.validation)}, "
            f"production={repr(self.production)})"
        )


def create_endpoint_from_url(
    url: str, dataplane_auth: DataplaneAuth, pod_name: Optional[str] = None
) -> DataplaneEndpoint:
    """Convenience function to create endpoint from URL, auth, and optional pod name."""
    return DataplaneEndpoint(url=url, dataplane_auth=dataplane_auth, pod_name=pod_name)

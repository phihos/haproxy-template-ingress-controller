"""
Data fetching utilities for the dashboard.

Handles collecting data from management socket, Prometheus metrics,
and Kubernetes resources via the kr8s Kubernetes API client.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import logging

from kr8s.objects import Pod, Deployment
import kr8s

from .compatibility import CompatibilityChecker, CompatibilityLevel

logger = logging.getLogger(__name__)

__all__ = ["DashboardDataFetcher"]


class DashboardDataFetcher:
    """Fetches data from various sources for the dashboard."""

    def __init__(
        self,
        namespace: str,
        context: Optional[str] = None,
        deployment_name: str = "haproxy-template-ic",
    ):
        self.namespace = namespace
        self.context = context
        self.deployment_name = deployment_name
        self.compatibility_checker = CompatibilityChecker()

        # Cache for performance
        self._cache: Dict[str, Tuple[datetime, Any]] = {}
        self._cache_ttl = 2  # seconds

        # Cache for pod raw sync data to prevent toggling on fallback
        self._last_successful_pod_data = {}

        # Controller pod name and timing info for display in UI
        self._controller_pod_name: Optional[str] = None
        self._controller_pod_start_time: Optional[str] = None

    def _cache_pod_sync_status(self, pods: List[Dict[str, Any]]) -> None:
        """Cache raw pod sync data."""
        logger.debug(f"Caching sync status for {len(pods)} pods")
        for pod in pods:
            pod_name = pod.get("name")
            if pod_name and pod.get("sync_success") is not None:
                sync_success = pod.get("sync_success")
                last_sync = pod.get("last_sync")
                self._last_successful_pod_data[pod_name] = {
                    "sync_success": sync_success,
                    "last_sync": last_sync,
                }
                logger.debug(
                    f"Cached pod {pod_name}: sync_success={sync_success}, last_sync={last_sync}"
                )
            else:
                logger.debug(f"Skipping cache for pod {pod_name}: missing sync data")

    def _apply_cached_sync_data(
        self, pods: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Apply cached raw sync data to pods that have missing data."""
        logger.debug(f"Applying cached sync data to {len(pods)} pods")
        for pod in pods:
            pod_name = pod.get("name")
            current_sync_success = pod.get("sync_success")
            current_last_sync = pod.get("last_sync")

            if pod_name in self._last_successful_pod_data:
                cached = self._last_successful_pod_data[pod_name]
                used_cache = False

                # Use cached data if current data is missing or invalid
                if pod.get("sync_success") is None:
                    pod["sync_success"] = cached.get("sync_success")
                    used_cache = True
                if not pod.get("last_sync"):
                    pod["last_sync"] = cached.get("last_sync")
                    used_cache = True

                if used_cache:
                    logger.debug(
                        f"Applied cache to pod {pod_name}: current=({current_sync_success}, {current_last_sync}) -> cached=({cached.get('sync_success')}, {cached.get('last_sync')})"
                    )
                else:
                    logger.debug(
                        f"No cache needed for pod {pod_name}: has current data ({current_sync_success}, {current_last_sync})"
                    )
            else:
                logger.debug(f"No cache available for pod {pod_name}")
        return pods

    async def _get_socket_data_with_retry(
        self, command: str, max_retries: int = 1
    ) -> Dict[str, Any]:
        """Fetch data from management socket with retry logic."""
        logger.debug(
            f"Starting socket command '{command}' with max_retries={max_retries}"
        )
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                logger.debug(
                    f"Attempt {attempt + 1}/{max_retries + 1} for command '{command}'"
                )
                result = await self._get_socket_data(command)
                logger.debug(
                    f"Socket command '{command}' succeeded on attempt {attempt + 1}"
                )
                return result
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    logger.debug(
                        f"Attempt {attempt + 1} failed: {e}, retrying in 0.1s..."
                    )
                    # Short delay before retry
                    await asyncio.sleep(0.1)
                    continue
                else:
                    logger.debug(f"Final attempt {attempt + 1} failed: {e}")
                break

        # If all retries failed, raise the last error
        logger.debug(
            f"All {max_retries + 1} attempts failed for command '{command}', raising: {last_error}"
        )
        raise last_error

    async def initialize(self) -> CompatibilityLevel:
        """Initialize the data fetcher and check compatibility."""
        return await self.compatibility_checker.check_compatibility(
            self._get_socket_data
        )

    async def fetch_all_data(self) -> Dict[str, Any]:
        """Fetch all dashboard data based on compatibility level."""
        compatibility = self.compatibility_checker.compatibility_level

        if compatibility == CompatibilityLevel.FULL:
            return await self._fetch_optimized()
        elif compatibility == CompatibilityLevel.ENHANCED:
            return await self._fetch_hybrid()
        elif compatibility == CompatibilityLevel.BASIC:
            return await self._fetch_basic()
        else:  # LEGACY
            return await self._fetch_legacy()

    async def _get_socket_data(self, command: str) -> Dict[str, Any]:
        """Fetch data from management socket via kr8s pod exec."""
        cache_key = f"socket_{command}"
        logger.debug(f"Checking cache for command '{command}', cache_key='{cache_key}'")

        # Check cache first
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            age = (datetime.now(timezone.utc) - cached_time).total_seconds()
            if age < self._cache_ttl:
                logger.debug(f"Cache hit for command '{command}', age={age:.1f}s")
                return cached_data
            else:
                logger.debug(
                    f"Cache expired for command '{command}', age={age:.1f}s > {self._cache_ttl}s"
                )

        logger.debug(f"Cache miss for command '{command}', fetching from socket")

        try:
            # Get the deployment and its pods
            deployment = await Deployment.get(
                self.deployment_name, namespace=self.namespace
            )
            pods = deployment.pods()

            if not pods:
                logger.error(
                    f"No pods found for deployment '{self.deployment_name}' in namespace '{self.namespace}'"
                )
                return {"error": "No pods found for deployment"}

            # Use the first available pod (they should all be equivalent)
            pod = pods[0]
            pod_name = pod.metadata.name

            # Store the controller pod name and start time for UI display
            if self._controller_pod_name != pod_name:
                self._controller_pod_name = pod_name
                logger.debug(f"Controller pod name updated to: {pod_name}")

            # Extract and store pod start time
            pod_start_time = pod.status.get("startTime") if pod.status else None
            if pod_start_time and self._controller_pod_start_time != pod_start_time:
                self._controller_pod_start_time = pod_start_time
                logger.debug(f"Controller pod start time updated to: {pod_start_time}")

            logger.debug(f"Using pod '{pod_name}' for socket command '{command}'")

            # Execute the socat command to connect to management socket
            # Use sh -c with echo to pass the command through stdin
            exec_command = f"echo '{command}' | socat - UNIX-CONNECT:/run/haproxy-template-ic/management.sock"
            logger.debug(f"Executing: {exec_command}")

            exec_result = pod.exec(
                command=["sh", "-c", exec_command], container="controller"
            )

            # Log raw response info
            response_size = len(exec_result.stdout)
            logger.debug(
                f"Received {response_size} bytes from socket for command '{command}'"
            )
            if response_size > 0:
                # Log first few chars for debugging
                preview = str(exec_result.stdout[:100])
                if len(exec_result.stdout) > 100:
                    preview += "..."
                logger.debug(f"Response preview: {preview}")

            # Parse the JSON response
            data = json.loads(exec_result.stdout)
            logger.debug(
                f"Socket command '{command}' succeeded, result keys: {list(data.keys()) if isinstance(data, dict) else 'non-dict'}"
            )

            # Cache the result
            self._cache[cache_key] = (datetime.now(timezone.utc), data)
            logger.debug(
                f"Cached result for command '{command}', expires in {self._cache_ttl}s"
            )

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for command '{command}': {e}")
            logger.debug(
                f"Raw response that failed parsing: {exec_result.stdout if 'exec_result' in locals() else 'N/A'}"
            )
            return {"error": f"Invalid JSON response: {e}"}
        except Exception as e:
            logger.error(f"Failed to execute socket command '{command}': {e}")
            return {"error": f"Command failed: {e}"}

    async def _get_kubernetes_data(
        self, resource_type: str, label_selector: str = None
    ) -> Dict[str, Any]:
        """Fetch data from Kubernetes API via kr8s."""
        cache_key = f"k8s_{resource_type}_{label_selector or 'all'}"

        # Check cache first
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if (
                datetime.now(timezone.utc) - cached_time
            ).total_seconds() < self._cache_ttl:
                return cached_data

        try:
            # Get resources based on type
            if resource_type.lower() == "pods":
                if label_selector:
                    resources = list(
                        Pod.list(
                            namespace=self.namespace, label_selector=label_selector
                        )
                    )
                else:
                    resources = list(Pod.list(namespace=self.namespace))
            else:
                logger.error(f"Resource type '{resource_type}' not supported yet")
                return {"error": f"Unsupported resource type: {resource_type}"}

            # Create kubectl-like response structure
            data = {
                "apiVersion": "v1",
                "kind": "List",
                "items": [resource.raw for resource in resources],
            }

            # Cache the result
            self._cache[cache_key] = (datetime.now(timezone.utc), data)

            return data

        except Exception as e:
            logger.error(f"Failed to get {resource_type}: {e}")
            return {"error": f"API call failed: {e}"}

    def _parse_cpu(self, cpu_str: str) -> int:
        """Parse CPU string to nanocores."""
        if not cpu_str or cpu_str == "0":
            return 0

        try:
            if cpu_str.endswith("n"):
                return int(cpu_str[:-1])
            elif cpu_str.endswith("u"):
                return int(cpu_str[:-1]) * 1000
            elif cpu_str.endswith("m"):
                return int(cpu_str[:-1]) * 1000000
            else:
                # Assume cores, convert to nanocores
                return int(float(cpu_str) * 1000000000)
        except (ValueError, TypeError):
            return 0

    def _parse_memory(self, memory_str: str) -> int:
        """Parse memory string to bytes."""
        if not memory_str or memory_str == "0":
            return 0

        try:
            if memory_str.endswith("Ki"):
                return int(memory_str[:-2]) * 1024
            elif memory_str.endswith("Mi"):
                return int(memory_str[:-2]) * 1024 * 1024
            elif memory_str.endswith("Gi"):
                return int(memory_str[:-2]) * 1024 * 1024 * 1024
            elif memory_str.endswith("Ti"):
                return int(memory_str[:-2]) * 1024 * 1024 * 1024 * 1024
            elif memory_str.endswith("k"):
                return int(memory_str[:-1]) * 1000
            elif memory_str.endswith("M"):
                return int(memory_str[:-1]) * 1000 * 1000
            elif memory_str.endswith("G"):
                return int(memory_str[:-1]) * 1000 * 1000 * 1000
            elif memory_str.endswith("T"):
                return int(memory_str[:-1]) * 1000 * 1000 * 1000 * 1000
            else:
                # Assume bytes
                return int(memory_str)
        except (ValueError, TypeError):
            return 0

    def _format_cpu(self, nanocores: int) -> str:
        """Format nanocores to human readable CPU."""
        if nanocores == 0:
            return "0m"
        elif nanocores < 1000000:
            return f"{nanocores // 1000}u"
        elif nanocores < 1000000000:
            return f"{nanocores // 1000000}m"
        else:
            return f"{nanocores // 1000000000:.1f}"

    def _format_memory(self, bytes_val: int) -> str:
        """Format bytes to human readable memory."""
        if bytes_val == 0:
            return "0Ki"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val // 1024}Ki"
        elif bytes_val < 1024 * 1024 * 1024:
            return f"{bytes_val // (1024 * 1024)}Mi"
        else:
            return f"{bytes_val // (1024 * 1024 * 1024)}Gi"

    async def _get_pod_metrics(self) -> Dict[str, Any]:
        """Get pod metrics from metrics-server using kr8s API."""
        try:
            logger.debug("Fetching pod metrics using kr8s API")

            # Try kr8s approach first
            try:
                # Get the kr8s API client
                api = kr8s.api()

                # Make a raw API request to the metrics server
                # The metrics API endpoint is: /apis/metrics.k8s.io/v1beta1/namespaces/{namespace}/pods
                # Use relative path since kr8s adds its own base path
                endpoint = (
                    f"apis/metrics.k8s.io/v1beta1/namespaces/{self.namespace}/pods"
                )
                logger.debug(f"Making metrics API request to: {endpoint}")

                # Use the call_api method to make the raw API request
                async with api.call_api(method="GET", url=endpoint) as response:
                    response_data = await response

                # Parse the metrics response
                metrics_data = {}
                items = response_data.get("items", [])
                logger.debug(f"Received {len(items)} pod metrics from API")

                for item in items:
                    pod_name = item["metadata"]["name"]
                    containers = item.get("containers", [])

                    # Sum up metrics from all containers
                    total_cpu_nano = sum(
                        self._parse_cpu(c.get("usage", {}).get("cpu", "0"))
                        for c in containers
                    )
                    total_memory_bytes = sum(
                        self._parse_memory(c.get("usage", {}).get("memory", "0"))
                        for c in containers
                    )

                    metrics_data[pod_name] = {
                        "cpu": self._format_cpu(total_cpu_nano),
                        "memory": self._format_memory(total_memory_bytes),
                        "cpu_raw": total_cpu_nano,
                        "memory_raw": total_memory_bytes,
                    }

                    logger.debug(
                        f"Pod {pod_name}: CPU={metrics_data[pod_name]['cpu']}, Memory={metrics_data[pod_name]['memory']}"
                    )

                logger.debug(
                    f"Successfully fetched metrics for {len(metrics_data)} pods via kr8s API"
                )
                return {"metrics": metrics_data}

            except Exception as api_error:
                logger.debug(f"kr8s API approach failed: {api_error}")

                # Fallback to kubectl with context support
                logger.debug("Falling back to kubectl with context support")
                import subprocess

                # Build kubectl command with context if specified
                kubectl_cmd = [
                    "kubectl",
                    "top",
                    "pods",
                    "-n",
                    self.namespace,
                    "--no-headers",
                ]
                if self.context:
                    kubectl_cmd.extend(["--context", self.context])
                    logger.debug(f"Using kubectl context: {self.context}")

                logger.debug(f"Running command: {' '.join(kubectl_cmd)}")

                result = subprocess.run(
                    kubectl_cmd, capture_output=True, text=True, timeout=10
                )

                if result.returncode != 0:
                    logger.debug(f"kubectl top pods failed: {result.stderr}")
                    return {"error": f"kubectl top pods failed: {result.stderr}"}

                # Parse text output
                metrics_data = {}
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if not line.strip():
                        continue
                    parts = line.split()
                    if len(parts) >= 3:
                        pod_name = parts[0]
                        cpu = parts[1]
                        memory = parts[2]
                        metrics_data[pod_name] = {
                            "cpu": cpu,
                            "memory": memory,
                            "cpu_raw": 0,  # Not available in text mode
                            "memory_raw": 0,  # Not available in text mode
                        }

                logger.debug(
                    f"Successfully fetched metrics for {len(metrics_data)} pods via kubectl"
                )
                return {"metrics": metrics_data}

        except subprocess.TimeoutExpired:
            logger.debug("kubectl top pods timed out")
            return {"error": "Metrics request timed out"}
        except Exception as e:
            logger.debug(f"Failed to get pod metrics: {e}")
            return {"error": f"Metrics failed: {e}"}

    async def _fetch_optimized(self) -> Dict[str, Any]:
        """Fetch data using optimized dashboard commands (full compatibility)."""
        logger.debug("Starting optimized fetch with dump dashboard command")
        tasks = [
            ("dashboard", self._get_socket_data_with_retry("dump dashboard")),
            ("pods", self._get_kubernetes_data("pods", "app=haproxy")),
            ("metrics", self._get_pod_metrics()),
            ("deployments", self._get_socket_data_with_retry("dump deployments")),
            ("activity", self._get_socket_data_with_retry("dump activity")),
        ]

        results = {}
        for name, task in tasks:
            try:
                logger.debug(f"Fetching {name} data...")
                results[name] = await task
                logger.debug(f"Successfully fetched {name} data")
            except Exception as e:
                logger.error(f"Failed to fetch {name}: {e}")
                results[name] = {"error": str(e)}

        # If dashboard command worked, return the data directly - it's already in the correct format
        if "dashboard" in results and not results["dashboard"].get("error"):
            dashboard_data = results["dashboard"]
            logger.debug(
                f"Dashboard command succeeded, found {len(dashboard_data.get('pods', []))} pods in dashboard data"
            )

            # Transform dashboard pod data to match UI expectations
            if "pods" in dashboard_data and dashboard_data["pods"]:
                logger.debug(
                    f"Processing {len(dashboard_data['pods'])} pods from dashboard data"
                )
                # Cache raw sync data before enhancement
                self._cache_pod_sync_status(dashboard_data["pods"])
                dashboard_data["pods"] = self._enhance_dashboard_pods(
                    dashboard_data["pods"],
                    results.get("deployments", {}),
                    results.get("metrics", {}),
                    results.get("pods", {}),
                    results.get("activity", {}),
                )
            else:
                logger.debug("No pods found in dashboard data")

            # Enhance templates with additional types if dashboard data only has config
            if "templates" in dashboard_data and len(dashboard_data["templates"]) == 1:
                # Dashboard command likely only returned haproxy.cfg, fetch full template data
                try:
                    logger.debug(
                        "Dashboard templates incomplete, fetching additional template data"
                    )
                    config_data = await self._get_socket_data_with_retry("dump config")
                    # Pass deployment history to extract template info
                    deployment_data = results.get("deployments", {})
                    enhanced_templates = self._extract_template_info(
                        config_data, deployment_history=deployment_data
                    )
                    if len(enhanced_templates) > len(dashboard_data["templates"]):
                        logger.debug(
                            f"Enhanced templates from {len(dashboard_data['templates'])} to {len(enhanced_templates)}"
                        )
                        dashboard_data["templates"] = enhanced_templates
                except Exception as e:
                    logger.warning(f"Failed to enhance template data: {e}")

            # Add controller pod timing info to operator data
            if "operator" in dashboard_data:
                if self._controller_pod_name:
                    dashboard_data["operator"]["controller_pod_name"] = (
                        self._controller_pod_name
                    )
                    logger.debug(
                        f"Added controller pod name to operator data: {self._controller_pod_name}"
                    )

                if self._controller_pod_start_time:
                    dashboard_data["operator"]["controller_pod_start_time"] = (
                        self._controller_pod_start_time
                    )
                    logger.debug(
                        f"Added controller pod start time to operator data: {self._controller_pod_start_time}"
                    )

                # Add last deployment timestamp
                deployment_data = results.get("deployments", {})
                last_deployment_time = self._extract_last_deployment_time(
                    deployment_data
                )
                if last_deployment_time:
                    dashboard_data["operator"]["last_deployment_time"] = (
                        last_deployment_time
                    )
                    logger.debug(
                        f"Added last deployment time to operator data: {last_deployment_time}"
                    )

            # Add activity data if available
            activity_data = results.get("activity", {})
            if activity_data and not activity_data.get("error"):
                dashboard_data["activity"] = activity_data.get("activity", [])
                logger.debug(
                    f"Added {len(dashboard_data['activity'])} activity events from socket"
                )
            elif "activity" not in dashboard_data:
                dashboard_data["activity"] = []
                logger.debug("No activity data available, using empty list")

            # Collect any errors from other sources
            errors = []
            for source, data in results.items():
                if isinstance(data, dict) and data.get("error"):
                    errors.append(f"{source}: {data['error']}")
            if errors:
                dashboard_data.setdefault("errors", []).extend(errors)
                logger.debug(f"Added {len(errors)} errors from other sources: {errors}")

            return dashboard_data
        else:
            logger.debug(
                f"Dashboard command failed or missing, results: {list(results.keys())}, dashboard error: {results.get('dashboard', {}).get('error')}"
            )

        # Fallback to basic fetching
        return await self._fetch_basic()

    async def _fetch_hybrid(self) -> Dict[str, Any]:
        """Fetch data using some new commands with fallbacks."""
        logger.debug("Starting hybrid fetch with dump stats and dump all commands")
        # Try enhanced commands first
        tasks = [
            ("stats", self._get_socket_data("dump stats")),
            ("all", self._get_socket_data("dump all")),
            ("pods", self._get_kubernetes_data("pods", "app=haproxy")),
            ("activity", self._get_socket_data("dump activity")),
        ]

        results = {}
        for name, task in tasks:
            try:
                logger.debug(f"Fetching {name} data (hybrid mode)...")
                results[name] = await task
                logger.debug(f"Successfully fetched {name} data (hybrid mode)")
            except Exception as e:
                logger.error(f"Failed to fetch {name}: {e}")
                results[name] = {"error": str(e)}

        return self._process_hybrid_data(results)

    async def _fetch_basic(self) -> Dict[str, Any]:
        """Fetch data using existing dump commands."""
        logger.debug("Starting basic fetch with multiple dump commands")
        tasks = [
            ("all", self._get_socket_data("dump all")),
            ("config", self._get_socket_data("dump config")),
            ("deployments", self._get_socket_data("dump deployments")),
            ("pods", self._get_kubernetes_data("pods", "app=haproxy")),
            ("metrics", self._get_pod_metrics()),
            ("activity", self._get_socket_data("dump activity")),
        ]

        results = {}
        for name, task in tasks:
            try:
                logger.debug(f"Fetching {name} data (basic mode)...")
                results[name] = await task
                logger.debug(f"Successfully fetched {name} data (basic mode)")
            except Exception as e:
                logger.error(f"Failed to fetch {name}: {e}")
                results[name] = {"error": str(e)}

        return self._process_basic_data(results)

    async def _fetch_legacy(self) -> Dict[str, Any]:
        """Fetch minimal data for very old operators."""
        logger.debug("Starting legacy fetch with single dump all command")
        try:
            logger.debug("Fetching dump all data (legacy mode)...")
            all_data = await self._get_socket_data("dump all")
            logger.debug("Successfully fetched dump all data (legacy mode)")
            return self._process_legacy_data(all_data)
        except Exception as e:
            logger.error(f"Failed to fetch legacy data: {e}")
            return {"error": f"Legacy fetch failed: {e}"}

    def _transform_dashboard_data(
        self,
        dashboard_data: Dict[str, Any],
        k8s_pods: Dict[str, Any],
        pod_metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Transform raw dashboard data into the format expected by UI panels."""
        # Extract config and metadata from dashboard data
        config = dashboard_data.get("config", {})
        metadata = dashboard_data.get("metadata", {})
        indices = dashboard_data.get("indices", {})
        haproxy_config_context = dashboard_data.get("haproxy_config_context", {})

        # Transform operator info
        operator = {
            "status": "RUNNING" if config else "UNKNOWN",
            "namespace": self.namespace,
            "configmap_name": metadata.get("configmap_name", "unknown"),
            "version": "unknown",  # Could be enhanced later
        }

        # Transform pod data
        pods = self._extract_pod_info(k8s_pods, pod_metrics)

        # Transform resource data
        resources = {}
        for resource_type, resource_index in indices.items():
            if isinstance(resource_index, dict):
                # Count resources and extract namespaces
                total_count = sum(
                    len(v) if isinstance(v, list) else 1
                    for v in resource_index.values()
                )
                namespaces = list(
                    set(
                        key.split(":")[0] for key in resource_index.keys() if ":" in key
                    )
                )
                resources[resource_type] = {
                    "count": total_count,
                    "namespaces": namespaces[:10],  # Limit to first 10 for display
                }

        # Transform template info
        templates = {}
        rendered_content = haproxy_config_context.get("rendered_content", [])
        rendered_config = haproxy_config_context.get("rendered_config", {})

        # Add rendered maps and files
        for content in rendered_content:
            filename = content.get("filename", "unknown")
            templates[filename] = {
                "status": "rendered",
                "type": content.get("content_type", "unknown"),
                "size": len(content.get("content", "")),
            }

        # Add main config
        if rendered_config.get("content"):
            templates["haproxy.cfg"] = {
                "status": "rendered",
                "type": "config",
                "size": len(rendered_config["content"]),
            }

        return {
            "operator": operator,
            "pods": pods,
            "resources": resources,
            "templates": templates,
            "activity": [],  # Could be enhanced later
            "performance": {},  # Could be enhanced later
        }

    def _process_hybrid_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Process data from hybrid (enhanced) mode."""
        # Extract pod info and apply cached sync data
        pods = self._extract_pod_info(results.get("pods", {}))
        pods = self._apply_cached_sync_data(pods)

        # Extract activity data first so we can use it for resource stats
        activity = self._extract_activity_data(results.get("activity", {}))

        processed = {
            "operator": self._extract_operator_info(results.get("all", {})),
            "pods": pods,
            "resources": self._calculate_resource_stats(
                results.get("all", {}), activity
            ),
            "templates": self._extract_template_info(results.get("all", {})),
            "activity": activity,
            "performance": results.get("stats", {}).get("performance", {}),
            "errors": [],
        }

        # Add controller pod timing info to operator data
        if self._controller_pod_name:
            processed["operator"]["controller_pod_name"] = self._controller_pod_name

        if self._controller_pod_start_time:
            processed["operator"]["controller_pod_start_time"] = (
                self._controller_pod_start_time
            )

        # Add last deployment timestamp from deployments data
        deployment_data = results.get("deployments", {})
        last_deployment_time = self._extract_last_deployment_time(deployment_data)
        if last_deployment_time:
            processed["operator"]["last_deployment_time"] = last_deployment_time

        # Collect any errors
        for source, data in results.items():
            if isinstance(data, dict) and data.get("error"):
                processed["errors"].append(f"{source}: {data['error']}")

        return processed

    def _process_basic_data(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Process data from basic mode (existing commands only)."""
        all_data = results.get("all", {})

        # Extract pod info and apply cached sync data
        pods = self._extract_pod_info(
            results.get("pods", {}), results.get("metrics", {})
        )
        pods = self._apply_cached_sync_data(pods)

        # Extract activity data first so we can use it for resource stats
        activity = self._extract_activity_data(results.get("activity", {}))

        processed = {
            "operator": self._extract_operator_info(all_data),
            "pods": pods,
            "resources": self._calculate_resource_stats(all_data, activity),
            "templates": self._extract_template_info(
                all_data, results.get("config", {})
            ),
            "activity": activity,
            "performance": {},  # Not available in basic mode
            "deployments": results.get("deployments", {}),
            "errors": [],
        }

        # Add controller pod timing info to operator data
        if self._controller_pod_name:
            processed["operator"]["controller_pod_name"] = self._controller_pod_name

        if self._controller_pod_start_time:
            processed["operator"]["controller_pod_start_time"] = (
                self._controller_pod_start_time
            )

        # Add last deployment timestamp from deployments data
        deployment_data = results.get("deployments", {})
        last_deployment_time = self._extract_last_deployment_time(deployment_data)
        if last_deployment_time:
            processed["operator"]["last_deployment_time"] = last_deployment_time

        # Collect any errors
        for source, data in results.items():
            if isinstance(data, dict) and data.get("error"):
                processed["errors"].append(f"{source}: {data['error']}")

        return processed

    def _process_legacy_data(self, all_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data for legacy mode (minimal functionality)."""
        processed = {
            "operator": self._extract_operator_info(all_data),
            "pods": [],
            "resources": {},
            "templates": {},
            "activity": [],
            "performance": {},
            "errors": [],
        }

        # Add controller pod timing info to operator data
        if self._controller_pod_name:
            processed["operator"]["controller_pod_name"] = self._controller_pod_name

        if self._controller_pod_start_time:
            processed["operator"]["controller_pod_start_time"] = (
                self._controller_pod_start_time
            )

        # Legacy mode doesn't have deployment data, so last_deployment_time won't be available

        return processed

    def _extract_last_deployment_time(
        self, deployment_data: Dict[str, Any]
    ) -> Optional[str]:
        """Extract the most recent deployment timestamp from deployment history."""
        history_data = deployment_data.get("deployment_history", {})

        most_recent_timestamp = None
        for endpoint, deployment_info in history_data.items():
            if deployment_info.get("success"):
                timestamp = deployment_info.get("timestamp")
                if timestamp and (
                    not most_recent_timestamp or timestamp > most_recent_timestamp
                ):
                    most_recent_timestamp = timestamp

        return most_recent_timestamp

    def _extract_operator_info(self, all_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract operator information from dump all data."""
        config = all_data.get("config", {})
        metadata = all_data.get("metadata", {})

        return {
            "status": "RUNNING" if config else "UNKNOWN",
            "configmap_name": metadata.get("configmap_name", "unknown"),
            "version": "unknown",  # Will be filled by launcher if available
            "namespace": self.namespace,
        }

    def _extract_pod_info(
        self, k8s_pods: Dict[str, Any], pod_metrics: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Extract HAProxy pod information."""
        pods = []
        items = k8s_pods.get("items", []) if not k8s_pods.get("error") else []
        metrics = (
            pod_metrics.get("metrics", {})
            if pod_metrics and not pod_metrics.get("error")
            else {}
        )

        for pod in items:
            metadata = pod.get("metadata", {})
            status = pod.get("status", {})

            pod_name = metadata.get("name", "unknown")
            pod_metrics = metrics.get(pod_name, {})

            pods.append(
                {
                    "name": pod_name,
                    "status": status.get("phase", "Unknown"),
                    "ip": status.get("podIP", "N/A"),
                    "cpu": pod_metrics.get("cpu", "N/A"),
                    "memory": pod_metrics.get("memory", "N/A"),
                    "synced": "Unknown",  # Would come from deployment history
                    "start_time": status.get(
                        "startTime"
                    ),  # Pod start timestamp for uptime calculation
                }
            )

        return pods

    def _enhance_dashboard_pods(
        self,
        dashboard_pods: List[Dict[str, Any]],
        deployment_history: Dict[str, Any] = None,
        pod_metrics: Dict[str, Any] = None,
        k8s_pods_data: Dict[str, Any] = None,
        activity_data: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """Transform dashboard pod data to match UI expectations."""
        from datetime import datetime, timezone

        logger.debug(f"Enhancing {len(dashboard_pods)} dashboard pods")
        enhanced_pods = []

        # Extract metrics data if available
        metrics = (
            pod_metrics.get("metrics", {})
            if pod_metrics and not pod_metrics.get("error")
            else {}
        )
        logger.debug(
            f"Using metrics data for {len(metrics)} pods: {list(metrics.keys())}"
        )

        # Build IP-to-name mapping from Kubernetes data for metrics lookup
        ip_to_name_mapping = {}
        if k8s_pods_data and not k8s_pods_data.get("error"):
            k8s_items = k8s_pods_data.get("items", [])
            for k8s_pod in k8s_items:
                k8s_pod_name = k8s_pod.get("metadata", {}).get("name", "")
                k8s_pod_ip = k8s_pod.get("status", {}).get("podIP", "")
                if k8s_pod_name and k8s_pod_ip:
                    ip_to_name_mapping[k8s_pod_ip] = k8s_pod_name
            logger.debug(
                f"Built IP-to-name mapping for {len(ip_to_name_mapping)} pods: {ip_to_name_mapping}"
            )

        for pod in dashboard_pods:
            pod_name = pod.get("name", "unknown")
            pod_ip = pod.get("ip", "")

            # Try to get metrics by name first, then by IP mapping
            pod_metrics_data = metrics.get(pod_name, {})
            if not pod_metrics_data and pod_ip and pod_ip in ip_to_name_mapping:
                real_pod_name = ip_to_name_mapping[pod_ip]
                pod_metrics_data = metrics.get(real_pod_name, {})
                logger.debug(
                    f"Pod {pod_name} (IP {pod_ip}) mapped to real name {real_pod_name} for metrics lookup"
                )

            # Map dashboard fields to UI expectations
            enhanced_pod = {
                "name": pod_name,
                "status": "Running",  # Dashboard pods are typically running
                "ip": pod_ip or "N/A",
                "cpu": pod_metrics_data.get("cpu", "N/A"),  # Use metrics if available
                "memory": pod_metrics_data.get(
                    "memory", "N/A"
                ),  # Use metrics if available
            }

            logger.debug(
                f"Pod {pod_name}: CPU={enhanced_pod['cpu']}, Memory={enhanced_pod['memory']}"
            )

            # Add pod start time from original pod data if available, or merge from Kubernetes data
            enhanced_pod["start_time"] = pod.get("start_time")

            # If no start_time in dashboard data, try to get it from Kubernetes pod data
            if not enhanced_pod["start_time"] and k8s_pods_data:
                k8s_items = (
                    k8s_pods_data.get("items", [])
                    if not k8s_pods_data.get("error")
                    else []
                )
                for k8s_pod in k8s_items:
                    k8s_metadata = k8s_pod.get("metadata", {})
                    k8s_pod_name = k8s_metadata.get("name", "")
                    k8s_pod_ip = k8s_pod.get("status", {}).get("podIP", "")

                    # Match pod by name or by IP
                    if k8s_pod_name == pod_name or (pod_ip and k8s_pod_ip == pod_ip):
                        k8s_status = k8s_pod.get("status", {})
                        start_time = k8s_status.get("startTime")
                        if start_time:
                            enhanced_pod["start_time"] = start_time
                            logger.debug(
                                f"Pod {pod_name}: Merged startTime from Kubernetes: {start_time}"
                            )
                        break

            # Extract last reload timestamp from activity events
            enhanced_pod["last_reload_timestamp"] = None
            if activity_data and pod_name:
                # Try to match pod to reload events by endpoint URL
                pod_ip = pod.get("ip", "N/A")
                if pod_ip != "N/A":
                    # Look for reload events matching this pod's IP
                    events = activity_data.get("events", [])

                    # Find the most recent reload event for this endpoint
                    latest_reload_timestamp = None
                    possible_ports = [
                        "5555",
                        "5556",
                    ]  # Standard and alternative dataplane ports

                    for event in reversed(events):  # Start with most recent events
                        if event.get("type") == "RELOAD":
                            metadata = event.get("metadata", {})
                            endpoint = metadata.get("endpoint", "")

                            # Check if this event matches any of the possible endpoint URLs for this pod
                            for port in possible_ports:
                                expected_endpoint = f"http://{pod_ip}:{port}"
                                if endpoint == expected_endpoint:
                                    latest_reload_timestamp = event.get("timestamp")
                                    logger.debug(
                                        f"Pod {pod_name}: Found reload event at {latest_reload_timestamp} from activity data for endpoint {endpoint}"
                                    )
                                    break

                            if latest_reload_timestamp:
                                break  # Found the most recent reload for this pod

                    enhanced_pod["last_reload_timestamp"] = latest_reload_timestamp
                    if not latest_reload_timestamp:
                        logger.debug(
                            f"Pod {pod_name}: No reload events found for IP {pod_ip} (tried ports {possible_ports})"
                        )

            # Calculate sync status from sync_success and last_sync, using cache fallback
            original_sync_success = pod.get("sync_success")
            original_last_sync = pod.get("last_sync")
            sync_success = original_sync_success
            last_sync = original_last_sync

            logger.debug(
                f"Processing pod {pod_name}: original sync_success={original_sync_success}, last_sync={original_last_sync}"
            )

            # Use cached data if current data is missing or invalid
            if pod_name in self._last_successful_pod_data:
                cached = self._last_successful_pod_data[pod_name]
                if sync_success is None:
                    sync_success = cached.get("sync_success", False)
                    logger.debug(
                        f"Pod {pod_name}: Using cached sync_success={sync_success}"
                    )
                if not last_sync:
                    last_sync = cached.get("last_sync")
                    logger.debug(f"Pod {pod_name}: Using cached last_sync={last_sync}")

            # Default to False if still no sync_success value
            if sync_success is None:
                sync_success = False
                logger.debug(f"Pod {pod_name}: Defaulting sync_success to False")

            if not sync_success:
                enhanced_pod["synced"] = "Failed"
                logger.debug(f"Pod {pod_name}: sync_success=False -> synced=Failed")
            elif last_sync:
                try:
                    # Parse timestamp and format as time since last sync
                    sync_time = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
                    now = datetime.now(timezone.utc)
                    time_diff = now - sync_time

                    # Store additional metadata for potential future use
                    enhanced_pod["sync_timestamp"] = sync_time
                    enhanced_pod["sync_time_diff_seconds"] = time_diff.total_seconds()

                    # Format as human-readable time ago
                    if time_diff.total_seconds() < 60:
                        enhanced_pod["synced"] = (
                            f"{int(time_diff.total_seconds())}s ago"
                        )
                    elif time_diff.total_seconds() < 3600:
                        enhanced_pod["synced"] = (
                            f"{int(time_diff.total_seconds() / 60)}m ago"
                        )
                    elif time_diff.total_seconds() < 86400:
                        enhanced_pod["synced"] = (
                            f"{int(time_diff.total_seconds() / 3600)}h ago"
                        )
                    else:
                        enhanced_pod["synced"] = (
                            f"{int(time_diff.total_seconds() / 86400)}d ago"
                        )

                    logger.debug(
                        f"Pod {pod_name}: last_sync={last_sync} -> synced={enhanced_pod['synced']}"
                    )
                except Exception as e:
                    enhanced_pod["synced"] = "Unknown"
                    logger.debug(
                        f"Pod {pod_name}: Failed to parse last_sync={last_sync}: {e} -> synced=Unknown"
                    )
            else:
                enhanced_pod["synced"] = "Unknown"
                logger.debug(f"Pod {pod_name}: No last_sync data -> synced=Unknown")

            enhanced_pods.append(enhanced_pod)

        return enhanced_pods

    def _calculate_resource_stats(
        self, all_data: Dict[str, Any], activity: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Calculate resource statistics from indices."""
        # Try to get pre-calculated resource stats from the management socket first
        if "resources" in all_data:
            stats = all_data["resources"]
            # Enhance with last_change data from activity events
            self._add_last_change_to_stats(stats, activity or [])
            return stats

        # Fallback: calculate from raw indices if no pre-calculated stats available
        indices = all_data.get("indices", {})
        stats = {}

        for resource_type, resource_index in indices.items():
            if hasattr(resource_index, "__getitem__") and hasattr(
                resource_index, "__iter__"
            ):
                try:
                    # This handles kopf index structure where we need to iterate properly
                    namespaces = {}
                    total_count = 0

                    # Iterate through the kopf index
                    for key in resource_index:
                        try:
                            resources = resource_index[key]
                            # Handle both single resources and lists of resources
                            if not isinstance(resources, list):
                                resources = [resources]

                            for resource in resources:
                                if isinstance(resource, dict):
                                    total_count += 1
                                    # Extract namespace, handling kopf Body objects
                                    metadata = resource.get("metadata", {})
                                    if hasattr(metadata, "get"):
                                        ns = metadata.get("namespace", "default")
                                    else:
                                        ns = "default"
                                    namespaces[ns] = namespaces.get(ns, 0) + 1
                        except Exception as e:
                            logger.debug(
                                f"Error processing resource key {key} for {resource_type}: {e}"
                            )
                            continue

                    if total_count > 0:
                        # Try to calculate memory size if the resource_index has the get_memory_size method
                        memory_size = 0
                        if hasattr(resource_index, "get_memory_size"):
                            try:
                                memory_size = resource_index.get_memory_size()
                            except Exception as e:
                                logger.debug(
                                    f"Failed to calculate memory size for {resource_type}: {e}"
                                )

                        stats[resource_type] = {
                            "total": total_count,
                            "namespaces": dict(
                                sorted(
                                    namespaces.items(), key=lambda x: x[1], reverse=True
                                )[:5]
                            ),  # Top 5 namespaces
                            "namespace_count": len(namespaces),
                            "memory_size": memory_size,
                        }

                except Exception as e:
                    logger.warning(f"Error calculating stats for {resource_type}: {e}")
                    continue

        # Enhance with last_change data from activity events
        self._add_last_change_to_stats(stats, activity or [])

        return stats

    def _add_last_change_to_stats(
        self, stats: Dict[str, Any], activity: List[Dict[str, Any]]
    ) -> None:
        """Add last_change timestamps to resource stats from activity events."""
        from datetime import datetime, timezone

        # Track the most recent timestamp for each resource type
        last_changes = {}

        # Process activity events to find resource-related changes
        for event in activity:
            if not isinstance(event, dict):
                continue

            message = event.get("message", "")
            timestamp_str = event.get("timestamp")

            if not timestamp_str or not message:
                continue

            # Look for events that mention specific resource types
            # Extract resource type from event messages
            resource_type = None
            for res_type in stats.keys():
                # Check for plural and singular forms
                singular = res_type.rstrip("s") if res_type.endswith("s") else res_type
                if (
                    res_type.lower() in message.lower()
                    or singular.lower() in message.lower()
                ):
                    resource_type = res_type
                    break

            if not resource_type:
                continue

            try:
                # Parse timestamp
                if timestamp_str.endswith("Z"):
                    event_dt = datetime.fromisoformat(
                        timestamp_str.replace("Z", "+00:00")
                    )
                elif "+" in timestamp_str or "-" in timestamp_str[-6:]:
                    event_dt = datetime.fromisoformat(timestamp_str)
                else:
                    event_dt = datetime.fromisoformat(timestamp_str).replace(
                        tzinfo=timezone.utc
                    )

                # Keep track of the most recent change for this resource type
                if (
                    resource_type not in last_changes
                    or event_dt > last_changes[resource_type]
                ):
                    last_changes[resource_type] = event_dt

            except Exception as e:
                logger.debug(
                    f"Failed to parse activity timestamp '{timestamp_str}': {e}"
                )
                continue

        # Add last_change to each resource type's stats
        for resource_type, resource_stats in stats.items():
            if resource_type in last_changes:
                resource_stats["last_change"] = last_changes[resource_type].isoformat()
            else:
                # No activity found for this resource type, leave as None (will show "—" in UI)
                resource_stats["last_change"] = None

    def _extract_template_info(
        self,
        all_data: Dict[str, Any],
        config_data: Dict[str, Any] = None,
        deployment_history: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Extract template information from all template types."""
        config_context = config_data or all_data.get("haproxy_config_context", {})

        templates = {}

        # Process main HAProxy config
        rendered_config = config_context.get("rendered_config", {})
        if rendered_config and rendered_config.get("content"):
            templates["haproxy.cfg"] = {
                "name": "haproxy.cfg",
                "type": "config",
                "size": len(rendered_config["content"]),
                "status": "valid",
            }

        # Process map files
        rendered_maps = config_context.get("rendered_maps", [])
        if isinstance(rendered_maps, list):
            for map_data in rendered_maps:
                if isinstance(map_data, dict):
                    filename = map_data.get("filename", "unknown.map")
                    content = map_data.get("content", "")
                    templates[filename] = {
                        "name": filename,
                        "type": "map",
                        "size": len(content),
                        "status": "valid" if content else "empty",
                    }

        # Process other files (error pages, etc.)
        rendered_files = config_context.get("rendered_files", [])
        if isinstance(rendered_files, list):
            for file_data in rendered_files:
                if isinstance(file_data, dict):
                    filename = file_data.get("filename", "unknown.file")
                    content = file_data.get("content", "")
                    templates[filename] = {
                        "name": filename,
                        "type": "file",
                        "size": len(content),
                        "status": "valid" if content else "empty",
                    }

        # Process certificates
        rendered_certificates = config_context.get("rendered_certificates", [])
        if isinstance(rendered_certificates, list):
            for cert_data in rendered_certificates:
                if isinstance(cert_data, dict):
                    filename = cert_data.get("filename", "unknown.pem")
                    content = cert_data.get("content", "")
                    templates[filename] = {
                        "name": filename,
                        "type": "certificate",
                        "size": len(content),
                        "status": "valid" if content else "empty",
                    }

        # Fallback: Process legacy rendered_content if no other templates found
        if not templates:
            rendered_content = config_context.get("rendered_content", [])
            for content in rendered_content:
                if isinstance(content, dict):
                    name = content.get("name", "unknown")
                    templates[name] = {
                        "name": name,
                        "type": content.get("content_type", "unknown"),
                        "size": len(content.get("content", "")),
                        "status": "valid" if content.get("content") else "empty",
                    }

        # Add last change information from deployment history
        if deployment_history:
            self._add_last_change_info(templates, deployment_history)

        return templates

    def _add_last_change_info(
        self, templates: Dict[str, Any], deployment_history: Dict[str, Any]
    ) -> None:
        """Add last change information to templates from deployment history."""
        history_data = deployment_history.get("deployment_history", {})

        # Find the most recent actual change timestamp for each template across all endpoints
        template_timestamps = {}

        for endpoint, deployment_info in history_data.items():
            if deployment_info.get("success"):
                # Use template_change_timestamps if available (new format)
                change_timestamps = deployment_info.get(
                    "template_change_timestamps", {}
                )
                if change_timestamps:
                    for template_name, change_timestamp in change_timestamps.items():
                        if (
                            template_name not in template_timestamps
                            or change_timestamp > template_timestamps[template_name]
                        ):
                            template_timestamps[template_name] = change_timestamp
                # Fallback for legacy format (before change tracking) - only if no template_change_timestamps at all
                elif "template_hashes" in deployment_info:
                    timestamp = deployment_info.get("timestamp")
                    if timestamp:
                        # Only use deployment timestamp if we have no change tracking data yet
                        # This prevents the bug where all templates get current timestamp
                        for template_name in deployment_info["template_hashes"]:
                            if template_name not in template_timestamps:
                                template_timestamps[template_name] = timestamp

        # Add last_change timestamp to each template
        for template_name, template_info in templates.items():
            last_change = template_timestamps.get(template_name)
            template_info["last_change"] = last_change

    def _extract_activity_data(
        self, activity_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract activity events from socket dump activity data."""
        if activity_data and not activity_data.get("error"):
            activities = activity_data.get("activity", [])
            logger.debug(
                f"Extracted {len(activities)} activity events from socket data"
            )
            return activities
        elif activity_data and activity_data.get("error"):
            logger.debug(f"Activity data had error: {activity_data.get('error')}")
            return []
        else:
            logger.debug("No activity data available")
            return []

    async def get_template_source(self, template_name: str) -> Dict[str, Any]:
        """Get the source template content (Jinja2) for a given template."""
        logger.debug(f"Fetching template source for: {template_name}")
        try:
            result = await self._get_socket_data_with_retry(
                f"get template_source {template_name}"
            )
            logger.debug(
                f"Template source fetch result for {template_name}: {'success' if not result.get('error') else result.get('error')}"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to fetch template source for {template_name}: {e}")
            return {"error": f"Failed to fetch template source: {e}"}

    async def get_rendered_template(self, template_name: str) -> Dict[str, Any]:
        """Get the rendered content for a given template."""
        logger.debug(f"Fetching rendered template for: {template_name}")
        try:
            result = await self._get_socket_data_with_retry(
                f"get rendered_template {template_name}"
            )
            logger.debug(
                f"Rendered template fetch result for {template_name}: {'success' if not result.get('error') else result.get('error')}"
            )
            return result
        except Exception as e:
            logger.error(f"Failed to fetch rendered template for {template_name}: {e}")
            return {"error": f"Failed to fetch rendered template: {e}"}

    async def get_template_content(self, template_name: str) -> Dict[str, Any]:
        """Get both source and rendered content for a template."""
        logger.debug(f"Fetching complete template content for: {template_name}")

        # Fetch both source and rendered content concurrently
        source_task = self.get_template_source(template_name)
        rendered_task = self.get_rendered_template(template_name)

        try:
            source_result, rendered_result = await asyncio.gather(
                source_task, rendered_task
            )

            response = {
                "template_name": template_name,
                "source": None,
                "rendered": None,
                "type": "unknown",
                "errors": [],
            }

            # Process source result
            if source_result and not source_result.get("error"):
                source_data = source_result.get("result", {})
                response["source"] = source_data.get("source")
                response["type"] = source_data.get("type", "unknown")
            else:
                response["errors"].append(
                    f"Source: {source_result.get('error', 'Unknown error')}"
                )

            # Process rendered result
            if rendered_result and not rendered_result.get("error"):
                rendered_data = rendered_result.get("result", {})
                response["rendered"] = rendered_data.get("content")
                if response["type"] == "unknown":
                    response["type"] = rendered_data.get("type", "unknown")
            else:
                response["errors"].append(
                    f"Rendered: {rendered_result.get('error', 'Unknown error')}"
                )

            logger.debug(
                f"Template content fetch complete for {template_name}: source={'available' if response['source'] else 'unavailable'}, rendered={'available' if response['rendered'] else 'unavailable'}"
            )
            return response

        except Exception as e:
            logger.error(f"Failed to fetch template content for {template_name}: {e}")
            return {
                "template_name": template_name,
                "source": None,
                "rendered": None,
                "type": "unknown",
                "errors": [f"Exception: {e}"],
            }

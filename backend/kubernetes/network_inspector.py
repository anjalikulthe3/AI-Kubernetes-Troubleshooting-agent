from kubernetes.kubectl_executor import KubectlExecutor


class NetworkInspector:
    """Inspect services, endpoints, and common networking issues."""

    def __init__(self, executor: KubectlExecutor) -> None:
        self.executor = executor

    def inspect(self) -> dict:
        services_result = self.executor.run("get", "svc", "-A", "-o", "json")
        endpoints_result = self.executor.run("get", "endpoints", "-A", "-o", "json")

        if not services_result.success:
            return {
                "healthy": True,
                "findings": [],
                "error": KubectlExecutor.sanitize_error(
                    services_result.stderr, "Failed to list services"
                ),
            }

        services_payload = services_result.json_output()
        if not isinstance(services_payload, dict):
            return {
                "healthy": True,
                "findings": [],
                "error": "Unexpected kubectl response while listing services",
            }

        endpoints_map = self._build_endpoints_map(endpoints_result)
        findings: list[dict] = []

        for service in services_payload.get("items", []):
            service_findings = self._inspect_service(service, endpoints_map)
            findings.extend(service_findings)

        return {
            "healthy": len(findings) == 0,
            "total_services": len(services_payload.get("items", [])),
            "findings": findings,
            "summary": f"Found {len(findings)} networking issue(s)",
        }

    def _build_endpoints_map(self, endpoints_result) -> dict[tuple[str, str], dict]:
        endpoints_map: dict[tuple[str, str], dict] = {}
        if not endpoints_result.success:
            return endpoints_map

        payload = endpoints_result.json_output()
        if not isinstance(payload, dict):
            return endpoints_map

        for endpoint in payload.get("items", []):
            metadata = endpoint.get("metadata", {})
            namespace = metadata.get("namespace", "default")
            name = metadata.get("name", "")
            endpoints_map[(namespace, name)] = endpoint

        return endpoints_map

    def _inspect_service(
        self,
        service: dict,
        endpoints_map: dict[tuple[str, str], dict],
    ) -> list[dict]:
        metadata = service.get("metadata", {})
        spec = service.get("spec", {})
        namespace = metadata.get("namespace", "default")
        name = metadata.get("name", "unknown")
        service_type = spec.get("type", "ClusterIP")

        if service_type == "ExternalName":
            return []

        selector = spec.get("selector") or {}
        endpoint = endpoints_map.get((namespace, name))
        endpoint_addresses = self._count_ready_addresses(endpoint)

        findings: list[dict] = []

        if endpoint is None:
            findings.append(
                self._build_finding(
                    name,
                    namespace,
                    "missing_endpoints",
                    "Service has no Endpoints object; traffic routing may fail",
                )
            )
        elif endpoint_addresses == 0:
            findings.append(
                self._build_finding(
                    name,
                    namespace,
                    "missing_endpoints",
                    "Service has no ready endpoints",
                )
            )

        if selector and endpoint_addresses == 0:
            selector_issue = self._check_selector_match(namespace, selector)
            if selector_issue:
                findings.append(
                    self._build_finding(
                        name,
                        namespace,
                        "selector_mismatch",
                        selector_issue,
                    )
                )
            else:
                findings.append(
                    self._build_finding(
                        name,
                        namespace,
                        "dns_risk",
                        "Service exists but backing pods are missing; in-cluster DNS may resolve with no healthy targets",
                    )
                )

        if not selector and service_type in {"ClusterIP", "LoadBalancer", "NodePort"}:
            findings.append(
                self._build_finding(
                    name,
                    namespace,
                    "missing_selector",
                    "Service has no selector and may rely on manual endpoints",
                )
            )

        return findings

    def _count_ready_addresses(self, endpoint: dict | None) -> int:
        if not endpoint:
            return 0

        total = 0
        for subset in endpoint.get("subsets", []):
            total += len(subset.get("addresses", []))
        return total

    def _check_selector_match(self, namespace: str, selector: dict) -> str | None:
        label_selector = ",".join(f"{key}={value}" for key, value in selector.items())
        result = self.executor.run(
            "get",
            "pods",
            "-n",
            namespace,
            "-l",
            label_selector,
            "-o",
            "json",
        )
        if not result.success:
            return None

        payload = result.json_output()
        if not isinstance(payload, dict):
            return None

        matching_pods = payload.get("items", [])
        if not matching_pods:
            return f"No pods match service selector: {label_selector}"

        return None

    @staticmethod
    def _build_finding(
        service_name: str,
        namespace: str,
        issue_type: str,
        message: str,
    ) -> dict:
        return {
            "service": service_name,
            "namespace": namespace,
            "issue_type": issue_type,
            "message": message,
        }

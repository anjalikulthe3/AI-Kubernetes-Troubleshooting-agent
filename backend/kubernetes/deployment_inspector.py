from kubernetes.kubectl_executor import KubectlExecutor


class DeploymentInspector:
    """Inspect deployments for rollout and replica issues."""

    def __init__(self, executor: KubectlExecutor) -> None:
        self.executor = executor

    def inspect(self) -> dict:
        result = self.executor.run("get", "deployments", "-A", "-o", "json")
        if not result.success:
            return {
                "healthy": True,
                "total_deployments": 0,
                "problematic_deployments": [],
                "error": KubectlExecutor.sanitize_error(
                    result.stderr, "Failed to list deployments"
                ),
            }

        payload = result.json_output()
        if not isinstance(payload, dict):
            return {
                "healthy": True,
                "total_deployments": 0,
                "problematic_deployments": [],
                "error": "Unexpected kubectl response while listing deployments",
            }

        items = payload.get("items", [])
        problematic_deployments: list[dict] = []

        for deployment in items:
            issue = self._inspect_deployment(deployment)
            if issue:
                problematic_deployments.append(issue)

        return {
            "healthy": len(problematic_deployments) == 0,
            "total_deployments": len(items),
            "problematic_deployments": problematic_deployments,
        }

    def _inspect_deployment(self, deployment: dict) -> dict | None:
        metadata = deployment.get("metadata", {})
        spec = deployment.get("spec", {})
        status = deployment.get("status", {})

        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")
        desired_replicas = spec.get("replicas", 0) or 0
        available_replicas = status.get("availableReplicas", 0) or 0
        unavailable_replicas = status.get("unavailableReplicas", 0) or 0
        updated_replicas = status.get("updatedReplicas", 0) or 0

        issues: list[str] = []

        if available_replicas < desired_replicas:
            issues.append(
                f"Only {available_replicas}/{desired_replicas} replicas are available"
            )

        if unavailable_replicas > 0:
            issues.append(f"{unavailable_replicas} replica(s) unavailable")

        if updated_replicas < desired_replicas:
            issues.append(
                f"Rollout incomplete: {updated_replicas}/{desired_replicas} replicas updated"
            )

        for condition in status.get("conditions", []):
            if condition.get("status") != "False":
                continue

            condition_type = condition.get("type", "Unknown")
            if condition_type in {"Available", "Progressing"}:
                message = condition.get("message", "No details provided")
                issues.append(f"{condition_type} condition failed: {message}")

        if not issues:
            return None

        return {
            "name": name,
            "namespace": namespace,
            "desired_replicas": desired_replicas,
            "available_replicas": available_replicas,
            "unavailable_replicas": unavailable_replicas,
            "issues": issues,
        }

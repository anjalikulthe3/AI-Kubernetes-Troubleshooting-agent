from datetime import datetime, timezone

from kubernetes.kubectl_executor import KubectlExecutor

PROBLEMATIC_WAITING_REASONS = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "ContainerCreating",
    "CreateContainerConfigError",
    "InvalidImageName",
}

PROBLEMATIC_TERMINATED_REASONS = {"OOMKilled", "Error"}


class PodInspector:
    """Inspect pod status and detect unhealthy workloads."""

    def __init__(self, executor: KubectlExecutor) -> None:
        self.executor = executor

    def inspect(self) -> dict:
        result = self.executor.run("get", "pods", "-A", "-o", "json")
        if not result.success:
            return {
                "healthy": True,
                "total_pods": 0,
                "problematic_pods": [],
                "error": KubectlExecutor.sanitize_error(result.stderr, "Failed to list pods"),
            }

        payload = result.json_output()
        if not isinstance(payload, dict):
            return {
                "healthy": True,
                "total_pods": 0,
                "problematic_pods": [],
                "error": "Unexpected kubectl response while listing pods",
            }

        items = payload.get("items", [])
        problematic_pods: list[dict] = []

        for pod in items:
            issues = self._collect_pod_issues(pod)
            for issue in issues:
                problematic_pods.append(issue)

        return {
            "healthy": len(problematic_pods) == 0,
            "total_pods": len(items),
            "problematic_pods": problematic_pods,
        }

    def _collect_pod_issues(self, pod: dict) -> list[dict]:
        metadata = pod.get("metadata", {})
        status = pod.get("status", {})
        namespace = metadata.get("namespace", "default")
        name = metadata.get("name", "unknown")
        phase = status.get("phase", "Unknown")

        issues: list[dict] = []

        if phase == "Pending":
            issues.append(self._build_issue(name, namespace, "Pending", "Pod is stuck in Pending phase"))

        if phase == "Failed":
            issues.append(self._build_issue(name, namespace, "Error", "Pod is in Failed phase"))

        for container_status in status.get("containerStatuses", []):
            issues.extend(self._inspect_container_status(name, namespace, container_status))

        for container_status in status.get("initContainerStatuses", []):
            issues.extend(self._inspect_container_status(name, namespace, container_status, init=True))

        return issues

    def _inspect_container_status(
        self,
        pod_name: str,
        namespace: str,
        container_status: dict,
        init: bool = False,
    ) -> list[dict]:
        issues: list[dict] = []
        container_name = container_status.get("name", "unknown")
        prefix = "init container" if init else "container"

        state = container_status.get("state", {})
        waiting = state.get("waiting", {})
        waiting_reason = waiting.get("reason")
        if waiting_reason in PROBLEMATIC_WAITING_REASONS:
            message = waiting.get("message", f"{prefix} is waiting with reason {waiting_reason}")
            if waiting_reason == "ContainerCreating" and not self._is_container_creating_stuck(waiting):
                return issues
            issues.append(
                self._build_issue(
                    pod_name,
                    namespace,
                    waiting_reason,
                    f"{prefix} '{container_name}': {message}",
                )
            )

        terminated = state.get("terminated", {})
        terminated_reason = terminated.get("reason")
        if terminated_reason in PROBLEMATIC_TERMINATED_REASONS:
            message = terminated.get("message", f"{prefix} terminated with reason {terminated_reason}")
            issues.append(
                self._build_issue(
                    pod_name,
                    namespace,
                    terminated_reason,
                    f"{prefix} '{container_name}': {message}",
                )
            )

        last_state = container_status.get("lastState", {}).get("terminated", {})
        last_reason = last_state.get("reason")
        if last_reason in PROBLEMATIC_TERMINATED_REASONS and not issues:
            message = last_state.get("message", f"{prefix} previously terminated with {last_reason}")
            issues.append(
                self._build_issue(
                    pod_name,
                    namespace,
                    last_reason,
                    f"{prefix} '{container_name}': {message}",
                )
            )

        return issues

    def _is_container_creating_stuck(self, waiting: dict) -> bool:
        """Treat long-running ContainerCreating states as stuck."""
        started_at = waiting.get("startedAt") or waiting.get("lastTransitionTime")
        if not started_at:
            return True

        try:
            started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        except ValueError:
            return True

        elapsed = datetime.now(timezone.utc) - started
        return elapsed.total_seconds() >= 120

    @staticmethod
    def _build_issue(name: str, namespace: str, status: str, detail: str) -> dict:
        return {
            "name": name,
            "namespace": namespace,
            "status": status,
            "detail": detail,
        }

from kubernetes.kubectl_executor import KubectlExecutor

PROBLEMATIC_EVENT_REASONS = {
    "FailedScheduling",
    "BackOff",
    "FailedMount",
    "FailedPull",
    "ErrImagePull",
    "Unhealthy",
}


class EventsAnalyzer:
    """Analyze Kubernetes events for troubleshooting signals."""

    def __init__(self, executor: KubectlExecutor) -> None:
        self.executor = executor

    def analyze(self) -> dict:
        result = self.executor.run(
            "get",
            "events",
            "-A",
            "--sort-by=.lastTimestamp",
            "-o",
            "json",
        )
        if not result.success:
            return {
                "healthy": True,
                "findings": [],
                "error": KubectlExecutor.sanitize_error(result.stderr, "Failed to list events"),
            }

        payload = result.json_output()
        if not isinstance(payload, dict):
            return {
                "healthy": True,
                "findings": [],
                "error": "Unexpected kubectl response while listing events",
            }

        findings: list[dict] = []
        for event in payload.get("items", []):
            finding = self._inspect_event(event)
            if finding:
                findings.append(finding)

        return {
            "healthy": len(findings) == 0,
            "total_events_scanned": len(payload.get("items", [])),
            "findings": findings[-25:],
            "summary": f"Found {len(findings)} relevant event(s)",
        }

    def _inspect_event(self, event: dict) -> dict | None:
        reason = event.get("reason", "")
        if reason not in PROBLEMATIC_EVENT_REASONS:
            return None

        involved = event.get("involvedObject", {})
        return {
            "reason": reason,
            "type": event.get("type", "Unknown"),
            "namespace": event.get("metadata", {}).get("namespace", "default"),
            "object_kind": involved.get("kind", "Unknown"),
            "object_name": involved.get("name", "unknown"),
            "message": event.get("message", ""),
            "count": event.get("count", 1),
            "last_timestamp": event.get("lastTimestamp") or event.get("eventTime"),
        }

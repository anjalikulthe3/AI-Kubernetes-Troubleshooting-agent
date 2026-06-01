import re

from kubernetes.kubectl_executor import KubectlExecutor

LOG_TAIL_LINES = 80
MAX_EXCERPT_LINES = 40

HIGHLIGHT_PATTERNS = [
    r"Exception",
    r"Error",
    r"ERROR",
    r"Failed",
    r"failed",
    r"Connection refused",
    r"connection reset",
    r"No such file",
    r"not found",
    r"env",
    r"environment variable",
    r"ImagePull",
    r"ErrImagePull",
    r"CrashLoopBackOff",
    r"OOMKilled",
    r"startup",
    r"panic",
    r"Traceback",
]


class LogsCollector:
    """Fetch concise logs from failed or unhealthy pods."""

    def __init__(self, executor: KubectlExecutor) -> None:
        self.executor = executor
        self._highlight_regex = re.compile("|".join(HIGHLIGHT_PATTERNS), re.IGNORECASE)

    def collect(self, problematic_pods: list[dict]) -> dict:
        if not problematic_pods:
            return {"collected_logs": [], "summary": "No unhealthy pods found for log collection"}

        seen: set[tuple[str, str]] = set()
        collected_logs: list[dict] = []

        for pod in problematic_pods:
            key = (pod.get("namespace", "default"), pod.get("name", ""))
            if not key[1] or key in seen:
                continue
            seen.add(key)

            log_entry = self._collect_pod_logs(key[1], key[0])
            if log_entry:
                collected_logs.append(log_entry)

        return {
            "collected_logs": collected_logs,
            "summary": f"Collected logs for {len(collected_logs)} pod(s)",
        }

    def _collect_pod_logs(self, pod_name: str, namespace: str) -> dict | None:
        current = self._fetch_logs(pod_name, namespace, previous=False)
        previous = self._fetch_logs(pod_name, namespace, previous=True)

        combined = self._merge_log_sources(current, previous)
        if not combined:
            return {
                "pod": pod_name,
                "namespace": namespace,
                "log_excerpt": "",
                "highlights": [],
                "note": "No logs available for this pod",
            }

        excerpt = self._build_excerpt(combined)
        highlights = self._extract_highlights(combined)

        return {
            "pod": pod_name,
            "namespace": namespace,
            "log_excerpt": excerpt,
            "highlights": highlights[:10],
        }

    def _fetch_logs(self, pod_name: str, namespace: str, previous: bool) -> str:
        args = [
            "logs",
            pod_name,
            "-n",
            namespace,
            f"--tail={LOG_TAIL_LINES}",
        ]
        if previous:
            args.append("--previous")

        result = self.executor.run(*args)
        if result.success:
            return result.stdout.strip()
        return ""

    @staticmethod
    def _merge_log_sources(current: str, previous: str) -> str:
        sections: list[str] = []
        if current:
            sections.append(current)
        if previous and previous != current:
            sections.append(f"[previous container]\n{previous}")
        return "\n".join(sections).strip()

    def _build_excerpt(self, logs: str) -> str:
        lines = logs.splitlines()
        if len(lines) <= MAX_EXCERPT_LINES:
            return logs

        highlighted = [line for line in lines if self._highlight_regex.search(line)]
        if highlighted:
            return "\n".join(highlighted[-MAX_EXCERPT_LINES:])

        return "\n".join(lines[-MAX_EXCERPT_LINES:])

    def _extract_highlights(self, logs: str) -> list[str]:
        highlights: list[str] = []
        for line in logs.splitlines():
            if self._highlight_regex.search(line):
                cleaned = line.strip()
                if cleaned and cleaned not in highlights:
                    highlights.append(cleaned)
        return highlights

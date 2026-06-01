class ConfidenceEngine:
    """Score diagnosis confidence using correlated Kubernetes evidence."""

    def score(self, investigation: dict, diagnosis: dict) -> tuple[int, str]:
        llm_confidence = int(diagnosis.get("confidence", 60))
        evidence_points, evidence_reasons = self._score_evidence(investigation)

        adjusted = int(round((llm_confidence * 0.55) + (evidence_points * 0.45)))
        adjusted = max(0, min(100, adjusted))

        llm_reasoning = diagnosis.get("confidence_reasoning", "").strip()
        reasons = evidence_reasons.copy()
        if llm_reasoning:
            reasons.append(llm_reasoning)

        if not reasons:
            reasons.append("Confidence based on available investigation evidence.")

        reasoning = "\n".join(f"- {reason}" for reason in reasons)
        return adjusted, reasoning

    def _score_evidence(self, investigation: dict) -> tuple[int, list[str]]:
        points = 35
        reasons: list[str] = []

        pods = investigation.get("pods", {})
        logs = investigation.get("logs", {})
        events = investigation.get("events", {})
        deployments = investigation.get("deployments", {})
        network = investigation.get("network", {})

        if not pods.get("healthy") and pods.get("problematic_pods"):
            points += 15
            reasons.append("Unhealthy pod state confirms an active failure")

        log_highlights = [
            highlight
            for entry in logs.get("collected_logs", [])
            for highlight in entry.get("highlights", [])
        ]
        if log_highlights:
            points += 15
            reasons.append("Logs contain explicit error signals")

        if events.get("findings"):
            points += 10
            reasons.append("Kubernetes events corroborate the failure")

        if deployments.get("problematic_deployments"):
            points += 10
            reasons.append("Deployment health checks show rollout/replica issues")

        if network.get("findings"):
            points += 10
            reasons.append("Networking findings support the diagnosis")

        if pods.get("error") or events.get("error"):
            points -= 20
            reasons.append("Some investigation data was unavailable, reducing certainty")

        points = max(0, min(100, points))
        return points, reasons

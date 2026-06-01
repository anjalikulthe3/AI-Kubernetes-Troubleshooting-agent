import json
from pathlib import Path

SENIOR_SRE_SYSTEM_PROMPT = """You are a Senior Kubernetes SRE diagnosing production incidents.

Your job is to correlate Kubernetes evidence and produce an actionable diagnosis.

Rules:
- Be specific and deterministic. Avoid vague statements like "check your configuration".
- Correlate pods, logs, events, deployments, and networking together.
- Prefer the most likely root cause supported by multiple evidence sources.
- Suggest practical kubectl commands a beginner can run safely.
- Include prevention recommendations to avoid repeat incidents.
- If the cluster appears healthy, say so clearly and explain why.
- Never invent resources that are not present in the evidence.
- Do not expose secrets or API keys in your response.

Respond with valid JSON only using this schema:
{
  "root_cause": "short root cause statement",
  "explanation": "detailed explanation correlating evidence",
  "fix": "actionable fix steps",
  "kubectl_command": "single primary kubectl command",
  "prevention_recommendation": "how to prevent this in future",
  "confidence": 0,
  "confidence_reasoning": "why this confidence level is appropriate"
}
"""


class PromptBuilder:
    """Build structured prompts from Kubernetes investigation evidence."""

    def __init__(self, system_prompt_path: Path | None = None) -> None:
        self.system_prompt_path = system_prompt_path

    def build_messages(self, investigation: dict) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self.build_system_prompt()},
            {"role": "user", "content": self.build_user_prompt(investigation)},
        ]

    def build_system_prompt(self) -> str:
        if self.system_prompt_path and self.system_prompt_path.exists():
            return self.system_prompt_path.read_text(encoding="utf-8").strip()
        return SENIOR_SRE_SYSTEM_PROMPT

    def build_user_prompt(self, investigation: dict) -> str:
        evidence = self._format_evidence(investigation)
        return (
            "Analyze the following Kubernetes investigation evidence.\n"
            "Return JSON only.\n\n"
            f"{evidence}"
        )

    def _format_evidence(self, investigation: dict) -> str:
        sections = [
            ("POD STATUS", investigation.get("pods", {})),
            ("LOGS", investigation.get("logs", {})),
            ("EVENTS", investigation.get("events", {})),
            ("DEPLOYMENT HEALTH", investigation.get("deployments", {})),
            ("NETWORKING FINDINGS", investigation.get("network", {})),
        ]

        formatted_sections: list[str] = []
        for title, payload in sections:
            formatted_sections.append(
                f"## {title}\n{json.dumps(payload, indent=2, default=str)}"
            )

        return "\n\n".join(formatted_sections)

import json
import re

from loguru import logger

from ai.llm_client import LLMClientError, OpenRouterClient
from ai.prompt_builder import PromptBuilder


class RootCauseAnalyzer:
    """Analyze investigation evidence and determine the most likely root cause."""

    def __init__(
        self,
        llm_client: OpenRouterClient | None = None,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.llm_client = llm_client or OpenRouterClient()
        self.prompt_builder = prompt_builder or PromptBuilder()

    def analyze(self, investigation: dict) -> dict:
        if self._cluster_appears_healthy(investigation):
            return self._healthy_cluster_diagnosis(investigation)

        try:
            messages = self.prompt_builder.build_messages(investigation)
            raw_response = self.llm_client.chat_completion(messages)
            parsed = self._parse_llm_response(raw_response)
            return self._normalize_diagnosis(parsed)
        except LLMClientError as exc:
            logger.warning("LLM analysis unavailable, using heuristic fallback: {}", exc)
            return self._heuristic_analysis(investigation, str(exc))
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to parse LLM JSON, using heuristic fallback: {}", exc)
            return self._heuristic_analysis(
                investigation,
                "LLM returned invalid JSON; heuristic analysis applied.",
            )

    def _cluster_appears_healthy(self, investigation: dict) -> bool:
        sections = (
            investigation.get("pods", {}),
            investigation.get("events", {}),
            investigation.get("deployments", {}),
            investigation.get("network", {}),
        )
        has_errors = any(section.get("error") for section in sections)
        if has_errors:
            return False

        return all(
            section.get("healthy", True)
            for section in sections
        )

    def _healthy_cluster_diagnosis(self, investigation: dict) -> dict:
        return {
            "root_cause": "No active Kubernetes failure detected",
            "explanation": (
                "Pod, event, deployment, and network checks did not identify unhealthy "
                "workloads or corroborating failure signals in the collected evidence."
            ),
            "fix": "No immediate fix required. Re-run investigation if symptoms appear.",
            "kubectl_command": "kubectl get pods -A",
            "prevention_recommendation": (
                "Continue monitoring pod restarts, deployment rollouts, and service endpoints."
            ),
            "confidence": 85,
            "confidence_reasoning": (
                "High confidence because all investigation sections reported healthy status."
            ),
            "analysis_source": "rule_based",
        }

    def _parse_llm_response(self, content: str) -> dict:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("LLM response must be a JSON object")
        return parsed

    def _normalize_diagnosis(self, diagnosis: dict) -> dict:
        return {
            "root_cause": str(diagnosis.get("root_cause", "Unknown root cause")).strip(),
            "explanation": str(diagnosis.get("explanation", "")).strip(),
            "fix": str(diagnosis.get("fix", "")).strip(),
            "kubectl_command": str(diagnosis.get("kubectl_command", "")).strip(),
            "prevention_recommendation": str(
                diagnosis.get("prevention_recommendation", "")
            ).strip(),
            "confidence": int(diagnosis.get("confidence", 60)),
            "confidence_reasoning": str(
                diagnosis.get("confidence_reasoning", "")
            ).strip(),
            "analysis_source": "llm",
        }

    def _heuristic_analysis(self, investigation: dict, note: str) -> dict:
        pods = investigation.get("pods", {}).get("problematic_pods", [])
        logs = investigation.get("logs", {}).get("collected_logs", [])
        events = investigation.get("events", {}).get("findings", [])
        deployments = investigation.get("deployments", {}).get(
            "problematic_deployments", []
        )
        network = investigation.get("network", {}).get("findings", [])

        primary_pod = pods[0] if pods else None
        log_highlights = []
        for entry in logs:
            log_highlights.extend(entry.get("highlights", []))

        combined_log_text = " ".join(log_highlights).lower()

        if "environment variable" in combined_log_text or "env" in combined_log_text:
            resource = primary_pod or {"name": "app", "namespace": "default"}
            return {
                "root_cause": "Application startup failed due to a missing environment variable",
                "explanation": (
                    "Pod logs indicate a configuration error during startup. "
                    f"Evidence from pod '{resource['name']}' in namespace '{resource['namespace']}' "
                    "and log highlights reference missing environment configuration."
                ),
                "fix": "Add the missing environment variable to the deployment and restart the workload.",
                "kubectl_command": (
                    f"kubectl edit deployment {resource['name']} -n {resource['namespace']}"
                ),
                "prevention_recommendation": (
                    "Validate required environment variables in CI and use ConfigMaps/Secrets checks "
                    "before rollout."
                ),
                "confidence": 78,
                "confidence_reasoning": (
                    "Moderate-high confidence because pod failure state aligns with env-related log errors."
                ),
                "analysis_source": "heuristic",
                "analysis_note": note,
            }

        if primary_pod and primary_pod.get("status") in {
            "ImagePullBackOff",
            "ErrImagePull",
        }:
            return {
                "root_cause": "Container image cannot be pulled",
                "explanation": (
                    f"Pod '{primary_pod['name']}' in namespace '{primary_pod['namespace']}' "
                    f"is in {primary_pod['status']} state, which indicates an image pull failure."
                ),
                "fix": "Verify the image name, tag, registry credentials, and image pull secrets.",
                "kubectl_command": (
                    f"kubectl describe pod {primary_pod['name']} -n {primary_pod['namespace']}"
                ),
                "prevention_recommendation": (
                    "Pin image tags in deployments and test pulls in staging before production rollout."
                ),
                "confidence": 80,
                "confidence_reasoning": (
                    "High confidence because ImagePullBackOff directly indicates an image pull problem."
                ),
                "analysis_source": "heuristic",
                "analysis_note": note,
            }

        if deployments:
            deployment = deployments[0]
            return {
                "root_cause": "Deployment rollout is unhealthy",
                "explanation": "; ".join(deployment.get("issues", [])),
                "fix": "Inspect failing pods for the deployment and fix the underlying container error.",
                "kubectl_command": (
                    f"kubectl rollout status deployment/{deployment['name']} "
                    f"-n {deployment['namespace']}"
                ),
                "prevention_recommendation": (
                    "Use readiness probes and staged rollouts to catch failures before full deployment."
                ),
                "confidence": 70,
                "confidence_reasoning": (
                    "Moderate confidence because deployment replica mismatch confirms rollout failure."
                ),
                "analysis_source": "heuristic",
                "analysis_note": note,
            }

        if network:
            finding = network[0]
            return {
                "root_cause": "Service networking issue detected",
                "explanation": finding.get("message", "Networking issue found."),
                "fix": (
                    "Verify service selectors, endpoints, and backing pod labels match."
                ),
                "kubectl_command": (
                    f"kubectl describe svc {finding['service']} -n {finding['namespace']}"
                ),
                "prevention_recommendation": (
                    "Add integration tests that validate service-to-pod connectivity after deploy."
                ),
                "confidence": 68,
                "confidence_reasoning": (
                    "Moderate confidence because service/endpoints evidence indicates routing problems."
                ),
                "analysis_source": "heuristic",
                "analysis_note": note,
            }

        if events:
            event = events[-1]
            return {
                "root_cause": f"Kubernetes event indicates {event.get('reason')} failure",
                "explanation": event.get("message", "Relevant cluster event detected."),
                "fix": "Inspect the affected object and resolve the event-reported condition.",
                "kubectl_command": (
                    f"kubectl describe {event.get('object_kind', 'pod').lower()} "
                    f"{event.get('object_name')} -n {event.get('namespace')}"
                ),
                "prevention_recommendation": (
                    "Monitor warning events and alert on repeated BackOff or FailedScheduling signals."
                ),
                "confidence": 62,
                "confidence_reasoning": (
                    "Moderate confidence because event evidence exists but logs may be incomplete."
                ),
                "analysis_source": "heuristic",
                "analysis_note": note,
            }

        return {
            "root_cause": "Unable to determine a specific root cause from available evidence",
            "explanation": note,
            "fix": "Collect additional evidence with kubectl describe and kubectl logs for affected pods.",
            "kubectl_command": "kubectl get pods -A",
            "prevention_recommendation": (
                "Ensure application logs emit clear startup errors and configure liveness/readiness probes."
            ),
            "confidence": 40,
            "confidence_reasoning": "Low confidence because evidence is incomplete or ambiguous.",
            "analysis_source": "heuristic",
            "analysis_note": note,
        }

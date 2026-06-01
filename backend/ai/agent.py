from loguru import logger

from ai.confidence_engine import ConfidenceEngine
from ai.fix_recommendation import FixRecommendationEngine
from ai.llm_client import OpenRouterClient
from ai.prompt_builder import PromptBuilder
from ai.root_cause_analyzer import RootCauseAnalyzer


class KubernetesAgent:
    """Senior SRE-style AI agent for Kubernetes incident diagnosis."""

    def __init__(
        self,
        llm_client: OpenRouterClient | None = None,
        prompt_builder: PromptBuilder | None = None,
        root_cause_analyzer: RootCauseAnalyzer | None = None,
        fix_engine: FixRecommendationEngine | None = None,
        confidence_engine: ConfidenceEngine | None = None,
    ) -> None:
        self.llm_client = llm_client or OpenRouterClient()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.root_cause_analyzer = root_cause_analyzer or RootCauseAnalyzer(
            llm_client=self.llm_client,
            prompt_builder=self.prompt_builder,
        )
        self.fix_engine = fix_engine or FixRecommendationEngine()
        self.confidence_engine = confidence_engine or ConfidenceEngine()

    def diagnose(self, investigation: dict) -> dict:
        logger.info("Starting AI diagnosis")

        analysis = self.root_cause_analyzer.analyze(investigation)
        enhanced = self.fix_engine.enhance(analysis, investigation)
        confidence, confidence_reasoning = self.confidence_engine.score(
            investigation,
            enhanced,
        )

        diagnosis = {
            "root_cause": enhanced["root_cause"],
            "explanation": enhanced["explanation"],
            "fix": enhanced["fix"],
            "kubectl_command": enhanced["kubectl_command"],
            "prevention_recommendation": enhanced.get("prevention_recommendation", ""),
            "confidence": confidence,
            "confidence_reasoning": confidence_reasoning,
            "analysis_source": enhanced.get("analysis_source", "llm"),
        }

        if enhanced.get("analysis_note"):
            diagnosis["analysis_note"] = enhanced["analysis_note"]

        logger.info(
            "AI diagnosis complete: root_cause='{}' confidence={}%",
            diagnosis["root_cause"],
            diagnosis["confidence"],
        )
        return diagnosis


def analyze_cluster(investigation: dict) -> dict:
    """Analyze investigation evidence and return a diagnosis."""
    return KubernetesAgent().diagnose(investigation)


def generate_diagnosis(investigation: dict) -> dict:
    """Backward-compatible alias for AI diagnosis generation."""
    return analyze_cluster(investigation)

from loguru import logger

from ai.agent import KubernetesAgent
from services.investigation_service import InvestigationService


def investigate_cluster() -> dict:
    """Run Kubernetes investigation and AI diagnosis."""
    investigation_service = InvestigationService()
    investigation = investigation_service.run()

    agent = KubernetesAgent()
    diagnosis = agent.diagnose(investigation)

    logger.info("Investigation and diagnosis pipeline complete")
    return {
        "investigation": investigation,
        "diagnosis": diagnosis,
    }

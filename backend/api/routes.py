from fastapi import APIRouter, HTTPException
from loguru import logger

from ai.agent import KubernetesAgent
from core.config import settings
from kubernetes.cluster_lister import list_clusters
from models.schemas import (
    ClusterInfo,
    ClustersResponse,
    Diagnosis,
    HealthResponse,
    InvestigateRequest,
    InvestigateResponse,
    InvestigationPayload,
    ProgressEvent,
)
from services.investigation_service import InvestigationService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="healthy", service="ai-kubernetes-agent")


@router.get("/clusters", response_model=ClustersResponse)
def get_clusters() -> ClustersResponse:
    """Return all Kubernetes contexts found in the local kubeconfig."""
    try:
        raw = list_clusters(settings.kubeconfig_path)
        clusters = [ClusterInfo(**c) for c in raw]
        return ClustersResponse(clusters=clusters)
    except Exception as exc:
        logger.error("Failed to list clusters: {}", exc)
        return ClustersResponse(
            clusters=[],
            error=(
                "Unable to read kubeconfig. "
                "Please verify the KUBECONFIG_PATH setting and that the file exists."
            ),
        )


@router.post("/investigate", response_model=InvestigateResponse)
def investigate(request: InvestigateRequest | None = None) -> InvestigateResponse:
    context_name = (request.context_name or "") if request else ""
    progress_events: list[dict[str, str]] = []

    def on_progress(step: str, status: str) -> None:
        progress_events.append({"step": step, "status": status})

    try:
        investigation_service = InvestigationService(context=context_name)
        investigation = investigation_service.run(on_progress=on_progress)
    except Exception as exc:
        logger.error("Kubernetes investigation failed: {}", exc)
        error_message = _friendly_k8s_error(str(exc))
        raise HTTPException(status_code=502, detail=error_message) from exc

    on_progress("ai_reasoning", "running")
    try:
        agent = KubernetesAgent()
        diagnosis_payload = agent.diagnose(investigation)
    except Exception as exc:
        logger.error("AI diagnosis failed: {}", exc)
        raise HTTPException(
            status_code=502,
            detail=(
                "AI reasoning failed. "
                "Please check that OPENROUTER_API_KEY is configured and the model is reachable."
            ),
        ) from exc
    on_progress("ai_reasoning", "complete")
    on_progress("root_cause", "complete")

    response = InvestigateResponse(
        status="success",
        investigation=InvestigationPayload(**investigation),
        diagnosis=Diagnosis(**diagnosis_payload),
        progress=[ProgressEvent(**event) for event in progress_events],
    )

    if request and request.investigation_id:
        response.message = f"investigation_id={request.investigation_id}"

    return response


def _friendly_k8s_error(raw: str) -> str:
    msg = raw.lower()
    if "unable to connect to the server" in msg or "connection refused" in msg:
        return (
            "Unable to connect to Kubernetes cluster.\n\n"
            "Please verify:\n"
            "- kubeconfig path is correct\n"
            "- cluster is reachable\n"
            "- kubectl permissions are configured"
        )
    if "kubeconfig" in msg or "no such file" in msg:
        return (
            "kubeconfig file not found.\n\n"
            "Please verify:\n"
            "- KUBECONFIG_PATH is set correctly\n"
            "- The file exists and is readable"
        )
    if "kubectl binary not found" in msg:
        return (
            "kubectl is not installed or not on PATH.\n\n"
            "Install kubectl and restart the backend."
        )
    if "timed out" in msg:
        return (
            "Kubernetes cluster did not respond in time.\n\n"
            "Please verify:\n"
            "- Cluster is running\n"
            "- Network connectivity is available"
        )
    if "unauthorized" in msg or "forbidden" in msg:
        return (
            "Authentication failed for Kubernetes cluster.\n\n"
            "Please verify:\n"
            "- kubeconfig credentials are valid\n"
            "- Service account has sufficient permissions"
        )
    return f"Kubernetes investigation failed: {raw}"

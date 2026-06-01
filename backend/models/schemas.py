from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class ProblematicPod(BaseModel):
    name: str
    namespace: str
    status: str
    detail: str | None = None


class PodInvestigation(BaseModel):
    healthy: bool
    total_pods: int = 0
    problematic_pods: list[ProblematicPod] = Field(default_factory=list)
    error: str | None = None


class CollectedLog(BaseModel):
    pod: str
    namespace: str
    log_excerpt: str = ""
    highlights: list[str] = Field(default_factory=list)
    note: str | None = None


class LogsInvestigation(BaseModel):
    collected_logs: list[CollectedLog] = Field(default_factory=list)
    summary: str = ""


class EventFinding(BaseModel):
    reason: str
    type: str
    namespace: str
    object_kind: str
    object_name: str
    message: str
    count: int = 1
    last_timestamp: str | None = None


class EventsInvestigation(BaseModel):
    healthy: bool
    total_events_scanned: int = 0
    findings: list[EventFinding] = Field(default_factory=list)
    summary: str = ""
    error: str | None = None


class ProblematicDeployment(BaseModel):
    name: str
    namespace: str
    desired_replicas: int
    available_replicas: int
    unavailable_replicas: int
    issues: list[str] = Field(default_factory=list)


class DeploymentsInvestigation(BaseModel):
    healthy: bool
    total_deployments: int = 0
    problematic_deployments: list[ProblematicDeployment] = Field(default_factory=list)
    error: str | None = None


class NetworkFinding(BaseModel):
    service: str
    namespace: str
    issue_type: str
    message: str


class NetworkInvestigation(BaseModel):
    healthy: bool
    total_services: int = 0
    findings: list[NetworkFinding] = Field(default_factory=list)
    summary: str = ""
    error: str | None = None


class InvestigationPayload(BaseModel):
    pods: PodInvestigation | dict[str, Any]
    logs: LogsInvestigation | dict[str, Any]
    events: EventsInvestigation | dict[str, Any]
    deployments: DeploymentsInvestigation | dict[str, Any]
    network: NetworkInvestigation | dict[str, Any]


class Diagnosis(BaseModel):
    root_cause: str
    explanation: str
    fix: str
    kubectl_command: str
    prevention_recommendation: str = ""
    confidence: int
    confidence_reasoning: str = ""
    analysis_source: str = "llm"
    analysis_note: str | None = None


class ClusterInfo(BaseModel):
    context_name: str
    cluster_name: str
    server: str
    is_current: bool


class ClustersResponse(BaseModel):
    clusters: list[ClusterInfo]
    error: str | None = None


class InvestigateRequest(BaseModel):
    investigation_id: str | None = None
    context_name: str | None = None


class ProgressEvent(BaseModel):
    step: str
    status: str


class InvestigateResponse(BaseModel):
    status: str
    investigation: InvestigationPayload
    diagnosis: Diagnosis | None = None
    progress: list[ProgressEvent] = Field(default_factory=list)
    message: str | None = None

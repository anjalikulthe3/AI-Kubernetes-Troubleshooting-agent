from collections.abc import Callable

from loguru import logger

from core.config import settings
from kubernetes.deployment_inspector import DeploymentInspector
from kubernetes.events_analyzer import EventsAnalyzer
from kubernetes.kubectl_executor import KubectlExecutor
from kubernetes.logs_collector import LogsCollector
from kubernetes.network_inspector import NetworkInspector
from kubernetes.pod_inspector import PodInspector


class InvestigationService:
    """Orchestrate Kubernetes evidence collection across all inspectors."""

    def __init__(
        self,
        executor: KubectlExecutor | None = None,
        context: str = "",
    ) -> None:
        self.executor = executor or KubectlExecutor(
            kubeconfig_path=settings.kubeconfig_path,
            context=context,
        )
        self.pod_inspector = PodInspector(self.executor)
        self.logs_collector = LogsCollector(self.executor)
        self.events_analyzer = EventsAnalyzer(self.executor)
        self.deployment_inspector = DeploymentInspector(self.executor)
        self.network_inspector = NetworkInspector(self.executor)

    def run(
        self,
        on_progress: Callable[[str, str], None] | None = None,
    ) -> dict:
        logger.info("Starting Kubernetes investigation")

        def report(step: str, status: str) -> None:
            if on_progress:
                on_progress(step, status)

        report("pods", "running")
        pods = self.pod_inspector.inspect()
        report("pods", "complete")
        logger.info(
            "Pod inspection complete: healthy={}, problematic={}",
            pods.get("healthy"),
            len(pods.get("problematic_pods", [])),
        )

        report("logs", "running")
        logs = self.logs_collector.collect(pods.get("problematic_pods", []))
        report("logs", "complete")
        logger.info("Log collection complete")

        report("events", "running")
        events = self.events_analyzer.analyze()
        report("events", "complete")
        logger.info(
            "Event analysis complete: findings={}",
            len(events.get("findings", [])),
        )

        report("deployments", "running")
        deployments = self.deployment_inspector.inspect()
        report("deployments", "complete")
        logger.info(
            "Deployment inspection complete: problematic={}",
            len(deployments.get("problematic_deployments", [])),
        )

        report("network", "running")
        network = self.network_inspector.inspect()
        report("network", "complete")
        logger.info(
            "Network inspection complete: findings={}",
            len(network.get("findings", [])),
        )

        investigation = {
            "pods": pods,
            "logs": logs,
            "events": events,
            "deployments": deployments,
            "network": network,
        }

        logger.info("Kubernetes investigation finished")
        return investigation

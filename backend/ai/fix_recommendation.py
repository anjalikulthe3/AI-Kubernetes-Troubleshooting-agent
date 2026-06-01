class FixRecommendationEngine:
    """Ensure fix recommendations are practical and Kubernetes-specific."""

    DEFAULT_COMMAND = "kubectl get pods -A"

    def enhance(self, diagnosis: dict, investigation: dict) -> dict:
        enhanced = dict(diagnosis)

        if not enhanced.get("fix"):
            enhanced["fix"] = self._default_fix(investigation)

        enhanced["kubectl_command"] = self._normalize_kubectl_command(
            enhanced.get("kubectl_command", ""),
            investigation,
        )

        if not enhanced.get("prevention_recommendation"):
            enhanced["prevention_recommendation"] = (
                "Add monitoring for pod restarts, failed rollouts, and missing service endpoints."
            )

        return enhanced

    def _default_fix(self, investigation: dict) -> str:
        pods = investigation.get("pods", {}).get("problematic_pods", [])
        if pods:
            pod = pods[0]
            return (
                f"Inspect pod '{pod['name']}' in namespace '{pod['namespace']}' and resolve "
                f"the reported {pod['status']} condition."
            )
        return "Review the investigation evidence and fix the first failing Kubernetes object."

    def _normalize_kubectl_command(self, command: str, investigation: dict) -> str:
        cleaned = command.strip()
        if cleaned.startswith("kubectl "):
            return cleaned

        pods = investigation.get("pods", {}).get("problematic_pods", [])
        if pods:
            pod = pods[0]
            return (
                f"kubectl describe pod {pod['name']} -n {pod['namespace']}"
            )

        deployments = investigation.get("deployments", {}).get(
            "problematic_deployments", []
        )
        if deployments:
            deployment = deployments[0]
            return (
                f"kubectl describe deployment {deployment['name']} "
                f"-n {deployment['namespace']}"
            )

        return self.DEFAULT_COMMAND

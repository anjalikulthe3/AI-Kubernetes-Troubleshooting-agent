import os
from pathlib import Path

import yaml
from loguru import logger


def _default_kubeconfig_path() -> str:
    return str(Path.home() / ".kube" / "config")


def list_clusters(kubeconfig_path: str = "") -> list[dict]:
    """
    Parse kubeconfig and return all contexts with cluster server info.

    Returns a list of dicts:
        {
            "context_name": str,
            "cluster_name": str,
            "server": str,
            "is_current": bool,
        }
    """
    path = kubeconfig_path or os.environ.get("KUBECONFIG", "") or _default_kubeconfig_path()

    if not path or not Path(path).exists():
        logger.warning("kubeconfig not found at path: {}", path)
        return []

    try:
        with open(path, encoding="utf-8") as fh:
            kubeconfig = yaml.safe_load(fh)
    except Exception as exc:
        logger.error("Failed to read kubeconfig: {}", exc)
        return []

    if not isinstance(kubeconfig, dict):
        return []

    current_context = kubeconfig.get("current-context", "")
    raw_contexts = kubeconfig.get("contexts") or []
    raw_clusters = kubeconfig.get("clusters") or []

    cluster_servers: dict[str, str] = {}
    for entry in raw_clusters:
        name = entry.get("name", "")
        server = (entry.get("cluster") or {}).get("server", "")
        if name:
            cluster_servers[name] = server

    results: list[dict] = []
    for entry in raw_contexts:
        context_name = entry.get("name", "")
        ctx = entry.get("context") or {}
        cluster_name = ctx.get("cluster", "")
        server = cluster_servers.get(cluster_name, "")
        results.append(
            {
                "context_name": context_name,
                "cluster_name": cluster_name,
                "server": server,
                "is_current": context_name == current_context,
            }
        )

    logger.info("Found {} cluster contexts in kubeconfig", len(results))
    return results

import json
import subprocess
from dataclasses import dataclass

from loguru import logger


@dataclass
class KubectlResult:
    success: bool
    stdout: str
    stderr: str
    return_code: int
    command: list[str]

    def json_output(self) -> dict | list | None:
        if not self.stdout.strip():
            return None
        try:
            return json.loads(self.stdout)
        except json.JSONDecodeError:
            logger.warning("Failed to parse kubectl output as JSON")
            return None


class KubectlExecutor:
    """Safely run kubectl commands and return structured results."""

    def __init__(
        self,
        kubeconfig_path: str = "",
        context: str = "",
        timeout: int = 60,
    ) -> None:
        self.kubeconfig_path = kubeconfig_path
        self.context = context
        self.timeout = timeout

    def _build_command(self, *args: str) -> list[str]:
        command = ["kubectl"]
        if self.kubeconfig_path:
            command.extend(["--kubeconfig", self.kubeconfig_path])
        if self.context:
            command.extend(["--context", self.context])
        command.extend(args)
        return command

    def run(self, *args: str, timeout: int | None = None) -> KubectlResult:
        command = self._build_command(*args)
        logger.info("Running kubectl command: {}", " ".join(command))

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout or self.timeout,
                check=False,
            )
        except FileNotFoundError:
            message = "kubectl binary not found. Install kubectl and ensure it is on PATH."
            logger.error(message)
            return KubectlResult(
                success=False,
                stdout="",
                stderr=message,
                return_code=127,
                command=command,
            )
        except subprocess.TimeoutExpired:
            message = f"kubectl command timed out after {timeout or self.timeout}s"
            logger.error(message)
            return KubectlResult(
                success=False,
                stdout="",
                stderr=message,
                return_code=124,
                command=command,
            )

        result = KubectlResult(
            success=completed.returncode == 0,
            stdout=completed.stdout,
            stderr=completed.stderr,
            return_code=completed.returncode,
            command=command,
        )

        if result.success:
            logger.debug("kubectl command completed successfully")
        else:
            logger.warning(
                "kubectl command failed (exit {}): {}",
                result.return_code,
                result.stderr.strip() or result.stdout.strip(),
            )

        return result

    @staticmethod
    def sanitize_error(stderr: str, fallback: str = "kubectl command failed") -> str:
        if not stderr:
            return fallback

        lines = [line.strip() for line in stderr.splitlines() if line.strip()]
        for line in reversed(lines):
            if line.startswith("Unable to connect to the server:"):
                return line
            if line.startswith("error:"):
                return line.removeprefix("error:").strip()
            if "kubectl binary not found" in line:
                return line

        return lines[-1] if lines else fallback

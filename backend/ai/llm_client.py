import time

import httpx
from loguru import logger

from core.config import settings


class LLMClientError(Exception):
    """Raised when the LLM client cannot produce a response."""


class OpenRouterClient:
    """Call OpenRouter chat completions using HTTPX."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.openrouter_api_key
        self.model = model if model is not None else settings.openrouter_model
        self.base_url = (base_url or settings.openrouter_base_url).rstrip("/")
        self.timeout = timeout or settings.openrouter_timeout
        self.max_retries = max_retries or settings.openrouter_max_retries

    def chat_completion(self, messages: list[dict[str, str]]) -> str:
        if not self.api_key:
            raise LLMClientError(
                "OPENROUTER_API_KEY is not configured. Add it to backend/.env."
            )

        if not self.model:
            raise LLMClientError(
                "OPENROUTER_MODEL is not configured. Add it to backend/.env."
            )

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "AI Kubernetes Agent",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }

        last_error = "Unknown OpenRouter error"

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    "Calling OpenRouter model={} attempt={}/{}",
                    self.model,
                    attempt,
                    self.max_retries,
                )
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    data = response.json()

                content = data["choices"][0]["message"]["content"]
                if not content:
                    raise LLMClientError("OpenRouter returned an empty response")

                logger.info("OpenRouter response received successfully")
                return content.strip()

            except httpx.TimeoutException:
                last_error = f"OpenRouter request timed out after {self.timeout}s"
                logger.warning("{} (attempt {}/{})", last_error, attempt, self.max_retries)
            except httpx.HTTPStatusError as exc:
                last_error = self._extract_http_error(exc)
                logger.warning(
                    "OpenRouter HTTP error (attempt {}/{}): {}",
                    attempt,
                    self.max_retries,
                    last_error,
                )
                if exc.response.status_code in {400, 401, 403, 404}:
                    break
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                last_error = f"Unexpected OpenRouter response format: {exc}"
                logger.error(last_error)
                break
            except httpx.HTTPError as exc:
                last_error = f"OpenRouter request failed: {exc}"
                logger.warning(
                    "{} (attempt {}/{})",
                    last_error,
                    attempt,
                    self.max_retries,
                )

            if attempt < self.max_retries:
                time.sleep(attempt)

        raise LLMClientError(last_error)

    @staticmethod
    def _extract_http_error(exc: httpx.HTTPStatusError) -> str:
        try:
            payload = exc.response.json()
            error = payload.get("error", {})
            if isinstance(error, dict):
                message = error.get("message")
                if message:
                    return message
            if isinstance(error, str):
                return error
        except ValueError:
            pass

        return f"OpenRouter HTTP {exc.response.status_code}"

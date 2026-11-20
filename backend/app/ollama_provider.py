"""Ollama local LLM provider client."""

from __future__ import annotations

import time
from typing import Dict, List, Optional, Tuple
import httpx


class LLMProviderError(RuntimeError):
    """Raised when a local LLM provider cannot be reached or returns an invalid response."""


class OllamaProvider:
    """Communicates with a locally running Ollama server via /api/tags and /api/chat."""

    def __init__(self, base_url: str = "http://localhost:11434", timeout_seconds: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(timeout_seconds, connect=8.0)

    @property
    def chat_endpoint(self) -> str:
        return f"{self.base_url}/api/chat"

    @property
    def models_endpoint(self) -> str:
        return f"{self.base_url}/api/tags"

    async def list_models(self) -> Tuple[List[str], int]:
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
                resp = await client.get(self.models_endpoint)
                resp.raise_for_status()
                data = resp.json()
        except httpx.ConnectError as exc:
            raise LLMProviderError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Ensure Ollama is running (`ollama serve`) and the endpoint URL is correct."
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMProviderError(
                f"Connection to Ollama at {self.base_url} timed out."
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Ollama returned an HTTP error: {exc}") from exc

        latency_ms = int((time.perf_counter() - start) * 1000)
        models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        return models, latency_ms

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.75,
        max_tokens: int = 2400,
        top_p: float = 0.92,
        json_mode: bool = True,
        json_schema: Optional[Dict[str, object]] = None,
    ) -> str:
        if not model:
            raise LLMProviderError(
                "No Ollama model is selected. Open Settings, refresh available models, and choose a downloaded model (e.g. `ollama pull qwen2.5:1.5b` or `qwen2.5:3b`)."
            )
        payload: Dict[str, object] = {
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": "15m",
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
                "num_ctx": 2048,
                "repeat_penalty": 1.15,
            },
        }
        if json_mode:
            payload["format"] = json_schema if json_schema else "json"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(self.chat_endpoint, json=payload)
                if resp.status_code == 404:
                    raise LLMProviderError(
                        f"Ollama model '{model}' was not found on {self.base_url}. "
                        f"Run `ollama pull {model}` or select an installed model in Settings."
                    )
                resp.raise_for_status()
                data = resp.json()
        except LLMProviderError:
            raise
        except httpx.ConnectError as exc:
            raise LLMProviderError(
                f"Ollama is unreachable at {self.base_url}. Start Ollama locally to generate new questions; "
                "your saved questions, historical question bank, and practice history remain accessible offline."
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMProviderError(
                f"Ollama model '{model}' timed out after {int(self.timeout.read or 120)}s. "
                "Try increasing the timeout in Settings or using a faster quantized model."
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"Ollama request failed: {exc}") from exc

        message = data.get("message") or {}
        content: Optional[str] = message.get("content")
        if not content or not content.strip():
            raise LLMProviderError("Ollama returned an empty response.")
        return content.strip()

"""LM Studio and Custom OpenAI-compatible local LLM provider client."""

from __future__ import annotations

import asyncio
import time
from typing import Dict, List, Optional, Tuple
import httpx

from .ollama_provider import LLMProviderError


class OpenAICompatibleLocalProvider:
    """Communicates with LM Studio or any local OpenAI-compatible server."""

    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        api_key: str = "",
        timeout_seconds: int = 120,
        provider_label: str = "LM Studio",
    ) -> None:
        cleaned = base_url.rstrip("/")
        # Allow users to enter http://localhost:1234 or http://localhost:1234/v1
        if not cleaned.endswith("/v1") and provider_label == "LM Studio":
            cleaned = f"{cleaned}/v1"
        self.base_url = cleaned
        self.api_key = api_key.strip()
        self.timeout = httpx.Timeout(timeout_seconds, connect=8.0)
        self.provider_label = provider_label

    @property
    def chat_endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    @property
    def models_endpoint(self) -> str:
        return f"{self.base_url}/models"

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def list_models(self) -> Tuple[List[str], int]:
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0)) as client:
                resp = await client.get(self.models_endpoint, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
        except httpx.ConnectError as exc:
            raise LLMProviderError(
                f"Cannot connect to {self.provider_label} at {self.base_url}. "
                "Start the local server (in LM Studio: Developer -> Start Server) and verify the endpoint."
            ) from exc
        except httpx.TimeoutException as exc:
            raise LLMProviderError(
                f"Connection to {self.provider_label} at {self.base_url} timed out."
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"{self.provider_label} returned an HTTP error: {exc}") from exc

        latency_ms = int((time.perf_counter() - start) * 1000)
        raw_items = data.get("data", []) if isinstance(data, dict) else []
        models = []
        for m in raw_items:
            if isinstance(m, dict) and m.get("id"):
                raw_id = m["id"]
                if raw_id.startswith("models/"):
                    raw_id = raw_id[len("models/"):]
                models.append(raw_id)
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
                f"No model selected for {self.provider_label}. Load a model in {self.provider_label} "
                "and select it in Settings."
            )

        clean_model = model[len("models/"):] if model.startswith("models/") else model
        payload: Dict[str, object] = {
            "model": clean_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": False,
        }
        # Note: Some LM Studio / vLLM / llama.cpp models reject response_format=json_object
        # so we try with it if requested and automatically retry once without it on 400.
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        data = None
        max_attempts = 3
        for attempt_idx in range(max_attempts):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(self.chat_endpoint, json=payload, headers=self._headers())
                    if resp.status_code == 400 and json_mode:
                        payload.pop("response_format", None)
                        resp = await client.post(self.chat_endpoint, json=payload, headers=self._headers())
                    if resp.status_code in (503, 429) and attempt_idx < max_attempts - 1:
                        await asyncio.sleep(1.2 * (attempt_idx + 1))
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    break
            except httpx.ConnectError as exc:
                raise LLMProviderError(
                    f"{self.provider_label} is unreachable at {self.base_url}. "
                    "Ensure the server is running."
                ) from exc
            except httpx.TimeoutException as exc:
                if attempt_idx < max_attempts - 1:
                    await asyncio.sleep(1.0)
                    continue
                raise LLMProviderError(
                    f"{self.provider_label} model '{model}' timed out after {int(self.timeout.read or 120)}s."
                ) from exc
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (503, 429) and attempt_idx < max_attempts - 1:
                    await asyncio.sleep(1.2 * (attempt_idx + 1))
                    continue
                detail = ""
                if hasattr(exc, "response") and exc.response is not None:
                    detail = f" ({exc.response.text[:300]})"
                raise LLMProviderError(f"{self.provider_label} request failed: {exc}{detail}") from exc
            except httpx.HTTPError as exc:
                detail = ""
                if hasattr(exc, "response") and exc.response is not None:
                    detail = f" ({exc.response.text[:300]})"
                raise LLMProviderError(f"{self.provider_label} request failed: {exc}{detail}") from exc

        if not data:
            raise LLMProviderError(f"{self.provider_label} request failed after {max_attempts} retries.")

        choices = data.get("choices") or []
        if not choices:
            raise LLMProviderError(f"{self.provider_label} returned no completion choices.")
        content: Optional[str] = (choices[0].get("message") or {}).get("content")
        if not content or not content.strip():
            raise LLMProviderError(f"{self.provider_label} returned an empty response.")
        return content.strip()

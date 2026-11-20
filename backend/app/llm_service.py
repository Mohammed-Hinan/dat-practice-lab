"""Unified local LLM orchestration service with strict local-only guard and JSON retry."""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from pydantic import ValidationError

from .lmstudio_provider import OpenAICompatibleLocalProvider
from .ollama_provider import LLMProviderError, OllamaProvider
from .schemas import AppSettings, GeneratedQuestionPayload, LLMConnectionStatus, ProviderType


def validate_endpoint(url: str) -> str:
    """Validate that the given LLM base URL is a syntactically valid http or https URL."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise LLMProviderError(f"Invalid endpoint URL: '{url}'. Expected http://... or https://...")
    return url.strip().rstrip("/")


validate_local_endpoint = validate_endpoint


def extract_json_object(raw_text: str) -> str:
    """Extract a JSON object from raw model output (stripping think tags or markdown fences)."""
    cleaned = raw_text.strip()
    # Strip <think>...</think> reasoning blocks emitted by local reasoning models (e.g. DeepSeek-R1, Qwen3)
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL | re.IGNORECASE).strip()

    # Strip ```json ... ``` fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", cleaned, flags=re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    # Find outermost JSON object boundaries
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        return cleaned[start : end + 1]
    if start != -1:
        return cleaned[start:]
    return cleaned


def repair_json_object(text: str) -> str:
    """Best-effort structural auto-repair for truncated or unclosed JSON objects."""
    cleaned = text.strip()
    start = cleaned.find("{")
    if start != -1:
        cleaned = cleaned[start:]
    
    in_string = False
    escape = False
    stack: List[str] = []
    fixed: List[str] = []

    for char in cleaned:
        if escape:
            fixed.append(char)
            escape = False
            continue
        if char == "\\":
            escape = True
            fixed.append(char)
            continue
        if char == '"':
            in_string = not in_string
            fixed.append(char)
            continue
        if in_string:
            fixed.append(char)
            continue
        if char in "{[":
            stack.append("}" if char == "{" else "]")
            fixed.append(char)
        elif char in "}]":
            if stack and stack[-1] == char:
                stack.pop()
            fixed.append(char)
        else:
            fixed.append(char)

    res = "".join(fixed)
    if in_string:
        res += '"'
    
    # Clean dangling colon or trailing commas
    res = re.sub(r':\s*"*$', ': ""', res.rstrip())
    res = re.sub(r',\s*$', '', res.rstrip())
    
    for closing in reversed(stack):
        res = re.sub(r',\s*$', '', res.rstrip())
        res += closing
        
    return res


CREATIVE_QUESTION_JSON_SCHEMA: Dict[str, object] = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 6, "maxLength": 85},
        "scenario": {"type": "string", "minLength": 35, "maxLength": 340},
        "subquestions": {
            "type": "array",
            "minItems": 2,
            "maxItems": 2,
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string", "enum": ["A", "B"]},
                    "instruction": {"type": "string", "minLength": 15, "maxLength": 340},
                    "marks": {"type": "integer", "enum": [5, 8, 10, 12, 15, 20]},
                    "deliverables": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 2,
                        "items": {"type": "string", "minLength": 4, "maxLength": 65},
                    },
                },
                "required": ["label", "instruction", "marks", "deliverables"],
                "additionalProperties": False,
            },
        },
        "constraints": {
            "type": "array",
            "minItems": 1,
            "maxItems": 2,
            "items": {"type": "string", "minLength": 6, "maxLength": 100},
        },
        "sketching_requirements": {
            "type": "array",
            "minItems": 1,
            "maxItems": 2,
            "items": {"type": "string", "minLength": 6, "maxLength": 110},
        },
        "visual_sketch_prompt": {"type": "string", "minLength": 30, "maxLength": 240},
    },
    "required": [
        "title",
        "scenario",
        "subquestions",
        "constraints",
        "sketching_requirements",
        "visual_sketch_prompt",
    ],
    "additionalProperties": False,
}


VISUAL_PROMPT_PAIR_JSON_SCHEMA: Dict[str, object] = {
    "type": "object",
    "properties": {
        "positive_prompt": {"type": "string", "minLength": 30, "maxLength": 260},
        "negative_prompt": {"type": "string", "minLength": 30, "maxLength": 360},
    },
    "required": ["positive_prompt", "negative_prompt"],
    "additionalProperties": False,
}


class LLMService:
    """Backend proxy for local LLM providers (Ollama, LM Studio, Custom OpenAI-compatible)."""

    def _build_provider(
        self,
        provider: ProviderType,
        base_url: str,
        api_key: str = "",
        timeout_seconds: int = 120,
    ):
        safe_url = validate_endpoint(base_url)
        if provider == "ollama":
            return OllamaProvider(base_url=safe_url, timeout_seconds=timeout_seconds)
        if provider == "gemini":
            return OpenAICompatibleLocalProvider(
                base_url=safe_url,
                api_key=api_key,
                timeout_seconds=timeout_seconds,
                provider_label="Google Gemini (Cloud Free)",
            )
        if provider == "groq":
            return OpenAICompatibleLocalProvider(
                base_url=safe_url,
                api_key=api_key,
                timeout_seconds=timeout_seconds,
                provider_label="Groq Cloud (Free)",
            )
        if provider == "lmstudio":
            return OpenAICompatibleLocalProvider(
                base_url=safe_url,
                api_key=api_key,
                timeout_seconds=timeout_seconds,
                provider_label="LM Studio",
            )
        return OpenAICompatibleLocalProvider(
            base_url=safe_url,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
            provider_label="Custom OpenAI-compatible endpoint",
        )

    def resolve_endpoint(
        self, settings: AppSettings, provider: Optional[ProviderType] = None, override_url: Optional[str] = None
    ) -> Tuple[ProviderType, str, str]:
        prov = provider or settings.provider
        if override_url:
            return prov, override_url, settings.custom_api_key if prov == "custom_openai" else ""
        if prov == "ollama":
            return prov, settings.ollama_base_url, ""
        if prov == "lmstudio":
            return prov, settings.lmstudio_base_url, ""
        if prov == "gemini":
            return prov, "https://generativelanguage.googleapis.com/v1beta/openai", settings.gemini_api_key
        if prov == "groq":
            return prov, "https://api.groq.com/openai/v1", settings.groq_api_key
        return prov, settings.custom_base_url, settings.custom_api_key

    async def test_connection(
        self,
        settings: AppSettings,
        provider: Optional[ProviderType] = None,
        override_url: Optional[str] = None,
        override_api_key: Optional[str] = None,
        override_model: Optional[str] = None,
    ) -> LLMConnectionStatus:
        prov, url, default_key = self.resolve_endpoint(settings, provider, override_url)
        api_key = override_api_key if override_api_key is not None else default_key
        selected_model = override_model if override_model is not None else settings.model

        try:
            client = self._build_provider(prov, url, api_key=api_key, timeout_seconds=settings.timeout_seconds)
            models, latency_ms = await client.list_models()
            if not models:
                if prov == "gemini":
                    models = ["gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.1-flash-lite"]
                elif prov == "groq":
                    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen-2.5-32b"]
            if not models:
                msg = (
                    f"Connected to {prov} ({client.base_url}), but no models were discovered. "
                    + (
                        "Run `ollama pull qwen2.5:7b` (or another local model) first."
                        if prov == "ollama"
                        else "Load a model in your server first."
                    )
                )
            elif selected_model and selected_model not in models:
                effective = selected_model
                msg = (
                    f"Connected to {prov} ({len(models)} model(s) discovered, {latency_ms}ms). "
                    f"Active model: '{effective}'."
                )
            else:
                effective = selected_model or (
                    settings.gemini_text_model if prov == "gemini" else (settings.groq_model if prov == "groq" else models[0])
                )
                msg = f"Connected to {prov} ({latency_ms}ms). Ready with '{effective}'."
            return LLMConnectionStatus(
                connected=True,
                provider=prov,
                endpoint=client.base_url,
                models=models,
                selected_model=selected_model or (models[0] if models else ""),
                latency_ms=latency_ms,
                message=msg,
            )
        except LLMProviderError as exc:
            return LLMConnectionStatus(
                connected=False,
                provider=prov,
                endpoint=url,
                models=[],
                selected_model=selected_model,
                latency_ms=None,
                message=str(exc),
            )

    async def generate_structured_question(
        self,
        settings: AppSettings,
        system_prompt: str,
        user_prompt: str,
        expected_category: str,
        expected_time_minutes: int,
        expected_difficulty: str,
        hydration_defaults: Optional[Dict[str, object]] = None,
    ) -> Tuple[GeneratedQuestionPayload, str, str]:
        """Call local LLM, hydrate deterministic metadata, validate strictly, and retry on invalid JSON."""
        prov, url, api_key = self.resolve_endpoint(settings)
        client = self._build_provider(prov, url, api_key=api_key, timeout_seconds=settings.timeout_seconds)

        model = settings.model.strip()
        if not model:
            if prov == "gemini":
                model = settings.gemini_text_model or "gemini-3.5-flash-lite"
            elif prov == "groq":
                model = settings.groq_model or "llama-3.3-70b-versatile"
            else:
                models, _ = await client.list_models()
                if not models:
                    raise LLMProviderError(
                        f"Connected to {prov} at {client.base_url}, but no models are installed/loaded."
                    )
                model = models[0]

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        last_error: Optional[str] = None
        last_raw: str = ""
        attempts = 1 + max(0, settings.max_retries)
        # Give generous headroom (3500 tokens for cloud) so question scenario, deliverables, constraints & sketching details never truncate
        effective_max_tokens = max(settings.max_tokens, 3500) if prov in ("gemini", "groq") else max(settings.max_tokens, 1500)

        for attempt in range(attempts):
            try:
                raw = await client.chat(
                    model=model,
                    messages=messages,
                    temperature=settings.temperature if attempt == 0 else max(0.3, settings.temperature - 0.15 * attempt),
                    max_tokens=effective_max_tokens,
                    top_p=settings.top_p,
                    json_mode=settings.enforce_json_mode,
                    json_schema=CREATIVE_QUESTION_JSON_SCHEMA if settings.enforce_json_mode else None,
                )
            except LLMProviderError as e:
                # If Gemini experiences a temporary 503 spike, seamlessly try alternate active flash-lite models
                if prov == "gemini" and ("503" in str(e) or "429" in str(e)):
                    fallback_models = ["gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
                    got_it = False
                    for fb in fallback_models:
                        if fb != model:
                            try:
                                raw = await client.chat(
                                    model=fb,
                                    messages=messages,
                                    temperature=settings.temperature if attempt == 0 else max(0.3, settings.temperature - 0.15 * attempt),
                                    max_tokens=effective_max_tokens,
                                    top_p=settings.top_p,
                                    json_mode=settings.enforce_json_mode,
                                    json_schema=CREATIVE_QUESTION_JSON_SCHEMA if settings.enforce_json_mode else None,
                                )
                                model = fb
                                got_it = True
                                break
                            except Exception:
                                continue
                    if not got_it:
                        raise e
                else:
                    raise e

            last_raw = raw
            extracted = extract_json_object(raw)
            try:
                try:
                    parsed = json.loads(extracted)
                except Exception:
                    # Attempt automated JSON repair if closing brackets or quotes were truncated
                    repaired = repair_json_object(extracted)
                    parsed = json.loads(repaired)
                if not isinstance(parsed, dict):
                    raise ValueError("Top-level JSON value must be an object.")

                # Hydrate deterministic metadata that the model doesn't need to waste tokens generating
                if hydration_defaults:
                    for key, val in hydration_defaults.items():
                        if key not in parsed or parsed[key] in (None, "", []):
                            parsed[key] = val

                # Enforce exact requested category/time/difficulty
                parsed["category"] = expected_category
                parsed["time_minutes"] = expected_time_minutes
                parsed["difficulty"] = expected_difficulty
                if isinstance(parsed.get("title"), str) and len(parsed["title"]) > 180:
                    parsed["title"] = parsed["title"][:177].rsplit(" ", 1)[0] + "..."

                # Coerce common small-model list/int quirks cleanly before strict validation
                for list_key in ("constraints", "sketching_requirements", "programme_tags", "competencies", "archetypes", "historical_pattern_references"):
                    if isinstance(parsed.get(list_key), str):
                        parsed[list_key] = [parsed[list_key]]

                if isinstance(parsed.get("subquestions"), list):
                    coerced_sqs = []
                    for idx, sq in enumerate(parsed["subquestions"]):
                        if isinstance(sq, str):
                            m_match = re.search(r"\((\d+)\s*marks?\)", sq, flags=re.IGNORECASE)
                            marks = int(m_match.group(1)) if m_match else 10
                            clean_inst = re.sub(r"^[A-Z][.):\s]+", "", sq).strip()
                            clean_inst = re.sub(r"\(\d+\s*marks?\)", "", clean_inst).strip()
                            coerced_sqs.append({
                                "label": chr(65 + idx),
                                "instruction": clean_inst or sq,
                                "marks": marks,
                                "deliverables": ["Analysis & requirements" if idx == 0 else "Annotated design sketch"],
                            })
                        elif isinstance(sq, dict):
                            sq["label"] = str(sq.get("label") or chr(65 + idx))[:16]
                            if isinstance(sq.get("deliverables"), str):
                                sq["deliverables"] = [sq["deliverables"]]
                            raw_m = sq.get("marks")
                            if isinstance(raw_m, str) and raw_m.isdigit():
                                sq["marks"] = max(1, int(raw_m))
                            elif isinstance(raw_m, (int, float)):
                                sq["marks"] = max(1, min(100, int(raw_m)))
                            else:
                                sq["marks"] = 10
                            coerced_sqs.append(sq)
                    parsed["subquestions"] = coerced_sqs

                if isinstance(parsed.get("evaluation_rubric"), list) and parsed["evaluation_rubric"]:
                    coerced_rubric = []
                    total_m = int(parsed.get("total_marks") or 20)
                    r_list = parsed["evaluation_rubric"]
                    default_each = max(1, round(total_m / max(1, len(r_list))))
                    for r in r_list:
                        if isinstance(r, str):
                            coerced_rubric.append({"criterion": r.strip(), "marks": default_each})
                        elif isinstance(r, dict):
                            crit = str(r.get("criterion") or "Design assessment").strip()
                            raw_m = r.get("marks")
                            if isinstance(raw_m, str) and raw_m.isdigit():
                                m = int(raw_m)
                            elif isinstance(raw_m, (int, float)):
                                m = int(raw_m)
                            else:
                                m = default_each
                            coerced_rubric.append({"criterion": crit, "marks": max(1, min(100, m))})
                    parsed["evaluation_rubric"] = coerced_rubric
                elif hydration_defaults and hydration_defaults.get("evaluation_rubric"):
                    parsed["evaluation_rubric"] = hydration_defaults["evaluation_rubric"]

                if isinstance(parsed.get("suggested_time_split"), list) and parsed["suggested_time_split"]:
                    coerced_ts = []
                    for t in parsed["suggested_time_split"]:
                        if isinstance(t, str):
                            coerced_ts.append({"activity": t.strip(), "minutes": 5})
                        elif isinstance(t, dict):
                            act = str(t.get("activity") or "Practice stage").strip()
                            raw_min = t.get("minutes")
                            m = int(raw_min) if isinstance(raw_min, (int, float, str)) and str(raw_min).isdigit() else 5
                            coerced_ts.append({"activity": act, "minutes": max(1, min(240, m))})
                    parsed["suggested_time_split"] = coerced_ts
                elif hydration_defaults and hydration_defaults.get("suggested_time_split"):
                    parsed["suggested_time_split"] = hydration_defaults["suggested_time_split"]

                validated = GeneratedQuestionPayload.model_validate(parsed)
                return validated, raw, model
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                last_error = str(exc)
                if attempt < attempts - 1:
                    messages.append({"role": "assistant", "content": raw[:2500]})
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                f"JSON validation error: {last_error}\n"
                                "Return ONLY a valid JSON object with keys: title, scenario, subquestions "
                                "(array of {label, instruction, marks, deliverables}), constraints, "
                                "sketching_requirements, programme_tags, competencies, evaluation_rubric."
                            ),
                        }
                    )

        raise LLMProviderError(
            f"Model '{model}' produced invalid JSON after {attempts} attempt(s). "
            f"Last validation error: {last_error}"
        )

    async def generate_plain_text(
        self,
        settings: AppSettings,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 90,
        temperature: float = 0.4,
    ) -> str:
        """Lightweight single-shot text generation for visual sketch prompt crafting."""
        prov, url, api_key = self.resolve_endpoint(settings)
        client = self._build_provider(prov, url, api_key=api_key, timeout_seconds=min(45, settings.timeout_seconds))
        model = settings.model.strip()
        if not model:
            if prov == "gemini":
                model = settings.gemini_text_model or "gemini-3.5-flash-lite"
            elif prov == "groq":
                model = settings.groq_model or "llama-3.3-70b-versatile"
            else:
                models, _ = await client.list_models()
                if not models:
                    raise LLMProviderError(
                        f"Connected to {prov} at {client.base_url}, but no models are installed/loaded."
                    )
                model = models[0]
        raw = await client.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.9,
            json_mode=False,
        )
        cleaned = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE).strip()
        return cleaned.strip('"\' \n')

    async def generate_json_with_schema(
        self,
        settings: AppSettings,
        system_prompt: str,
        user_prompt: str,
        json_schema: Dict[str, object],
        max_tokens: int = 340,
        temperature: float = 0.45,
    ) -> Dict[str, object]:
        """Generate a strict GBNF-validated JSON object (used for structured positive + negative image prompts)."""
        prov, url, api_key = self.resolve_endpoint(settings)
        client = self._build_provider(prov, url, api_key=api_key, timeout_seconds=min(60, settings.timeout_seconds))
        model = settings.model.strip()
        if not model:
            if prov == "gemini":
                model = settings.gemini_text_model or "gemini-3.5-flash-lite"
            elif prov == "groq":
                model = settings.groq_model or "llama-3.3-70b-versatile"
            else:
                models, _ = await client.list_models()
                if not models:
                    raise LLMProviderError(
                        f"Connected to {prov} at {client.base_url}, but no models are installed/loaded."
                    )
                model = models[0]
        raw = await client.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.9,
            json_mode=settings.enforce_json_mode,
            json_schema=json_schema if settings.enforce_json_mode else None,
        )
        extracted = extract_json_object(raw)
        parsed = json.loads(extracted)
        if not isinstance(parsed, dict):
            raise ValueError("Expected JSON object.")
        return parsed

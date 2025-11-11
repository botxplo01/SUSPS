import os
from typing import Optional
import requests

try:
    from huggingface_hub import InferenceClient
except Exception:  # pragma: no cover - optional dependency
    InferenceClient = None  # type: ignore


_DEFAULT_MODELS = [
    # default per project decision (license accepted)
    "meta-llama/Meta-Llama-3.1-8B-Instruct",
    # alternative generalist
    "HuggingFaceH4/zephyr-7b-beta",
    # seq2seq fallback (text2text)
    "google/flan-t5-large",
    # tiny fallback to avoid timeouts
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
]


FALLBACK_PREFIX = (
    "Advisory engine is temporarily unavailable; using rule-based summary."
)


class HFTextGenerator:
    def __init__(self, model: Optional[str] = None, timeout: float = 12.0):
        token = (
            os.getenv("HUGGINGFACE_API_KEY")
            or os.getenv("HF_API_TOKEN")
            or os.getenv("HUGGINGFACEHUB_API_TOKEN")
            or os.getenv("HF_API_KEY")  # user-provided name
        )
        self._token = token
        base_model = (
            model
            or os.getenv("HF_MODEL")
            or os.getenv("HF_MODEL_NAME")  # user-provided name
            or _DEFAULT_MODELS[0]
        )
        provider = (os.getenv("HF_CHAT_PROVIDER") or "").strip()
        if provider and ":" not in base_model:
            self.model = f"{base_model}:{provider}"
        else:
            self.model = base_model
        # Allow override from env
        try:
            timeout_env = float(os.getenv("HF_TIMEOUT", "0") or 0)
        except Exception:
            timeout_env = 0.0
        self.timeout = timeout_env or timeout
        self._client = None
        if InferenceClient and token:
            try:
                # Do not bind model here; we may switch to fallback on failure
                # Some versions accept token=, others api_key=; token works for >=0.23
                self._client = InferenceClient(token=token)
            except Exception:
                self._client = None

    def _is_text2text(self, model_name: str) -> bool:
        name = (model_name or "").lower()
        return "t5" in name or "flan" in name

    def _is_conversational(self, model_name: str) -> bool:
        name = (model_name or "").lower()
        # Heuristic: Llama 3.x instruct models expose chat-style interfaces
        force = os.getenv("HF_FORCE_TASK", "").lower() == "conversational"
        return force or ("meta-llama" in name or "llama-3" in name)

    # --- Chat Completions helpers (preferred for Llama Instruct) ---
    def _has_chat_completions(self) -> bool:
        try:
            chat = getattr(self._client, "chat", None)
            comps = getattr(chat, "completions", None)
            create = getattr(comps, "create", None)
            return callable(create)
        except Exception:
            return False

    def _chat_complete_hfhub(
        self, prompt: str, model_id: str, max_new_tokens: int, temperature: float
    ) -> Optional[str]:
        if not self._client or not self._has_chat_completions():
            return None
        try:
            completion = self._client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_new_tokens,
                temperature=temperature,
            )
            # huggingface_hub returns an object with .choices[0].message
            msg = completion.choices[0].message  # type: ignore[attr-defined]
            # message can be Mapping or object with .content
            if isinstance(msg, dict):
                return (msg.get("content") or "").strip() or None
            content = getattr(msg, "content", None)
            return (content or "").strip() or None
        except Exception:
            return None

    def _chat_complete_requests(
        self, prompt: str, model_id: str, max_new_tokens: int, temperature: float
    ) -> Optional[str]:
        if not self._token:
            return None
        try:
            r = requests.post(
                "https://router.huggingface.co/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._token}"},
                json={
                    "model": model_id,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_new_tokens,
                    "temperature": temperature,
                },
                timeout=self.timeout,
            )
            r.raise_for_status()
            data = r.json()
            choices = data.get("choices") or []
            if choices:
                msg = choices[0].get("message") or {}
                content = msg.get("content") or ""
                if content:
                    return str(content)
            return None
        except Exception:
            return None

    def generate(
        self, prompt: str, max_new_tokens: int = 400, temperature: float = 0.2
    ) -> str:
        # Try primary then fallback, with small backoff per model
        models = [self.model] + [m for m in _DEFAULT_MODELS if m != self.model]
        for m in models:
            tries = 3
            delay = 0.75
            for attempt in range(tries):
                try:
                    if not self._client and not self._token:
                        break
                    if self._is_text2text(m):
                        # Use text2text-generation for seq2seq models like FLAN-T5
                        if self._client:
                            resp = self._client.post(
                                json={
                                    "inputs": prompt,
                                    "parameters": {
                                        "max_new_tokens": max_new_tokens,
                                        "temperature": temperature,
                                    },
                                },
                                model=m,
                                task="text2text-generation",
                            )
                            # Possible shapes: list[{"generated_text": str}] or dict
                            if (
                                isinstance(resp, list)
                                and resp
                                and isinstance(resp[0], dict)
                            ):
                                out = resp[0].get("generated_text") or ""
                            elif isinstance(resp, dict):
                                out = (
                                    resp.get("generated_text")
                                    or resp.get("output_text")
                                    or ""
                                )
                            else:
                                out = str(resp)
                            if out.strip():
                                return out
                    elif self._is_conversational(m):
                        # Prefer Chat Completions for Llama-style instruct models
                        out = self._chat_complete_hfhub(
                            prompt, m, max_new_tokens, temperature
                        )
                        if not out:
                            out = self._chat_complete_requests(
                                prompt, m, max_new_tokens, temperature
                            )
                        if out and out.strip():
                            return out
                        # Fallback to classic HF conversational task
                        if self._client:
                            resp = self._client.post(
                                json={
                                    "inputs": {
                                        "past_user_inputs": [],
                                        "generated_responses": [],
                                        "text": prompt,
                                    },
                                    "parameters": {
                                        "max_new_tokens": max_new_tokens,
                                        "temperature": temperature,
                                    },
                                },
                                model=m,
                                task="conversational",
                            )
                            out = ""
                            if isinstance(resp, dict):
                                out = resp.get("generated_text") or ""
                                if not out:
                                    conv = resp.get("conversation") or {}
                                    gr = conv.get("generated_responses") or []
                                    if gr:
                                        out = gr[-1] or ""
                            else:
                                out = str(resp)
                            if out.strip():
                                return out
                    else:
                        if self._client:
                            out = self._client.text_generation(
                                prompt,
                                model=m,
                                max_new_tokens=max_new_tokens,
                                temperature=temperature,
                                top_p=0.9,
                                repetition_penalty=1.05,
                            )
                            return out if isinstance(out, str) else str(out)
                except Exception:
                    if attempt < tries - 1:
                        # backoff with jitter
                        import random
                        import time as _t

                        _t.sleep(delay + random.uniform(0, 0.25))
                        delay *= 1.8
                        continue
                    else:
                        break
        # Fallback: minimal deterministic advisory text
        return (
            f"{FALLBACK_PREFIX}\n\n"
            "Key trends: see recent peaks, dips, and changes; prioritize mitigation for sustained increases in congestion, demand spikes, and AQI elevations.\n"
            "Actions: optimize signal timing on peak corridors, stagger energy loads during evening peaks, increase public transit headways during commute windows, and prepare heat-health messaging during forecasted hot days."
        )

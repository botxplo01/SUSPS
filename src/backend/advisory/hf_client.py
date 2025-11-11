import os
from typing import Optional

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
        self.model = (
            model
            or os.getenv("HF_MODEL")
            or os.getenv("HF_MODEL_NAME")  # user-provided name
            or _DEFAULT_MODELS[0]
        )
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
                self._client = InferenceClient(token=token)
            except Exception:
                self._client = None

    def _is_text2text(self, model_name: str) -> bool:
        name = (model_name or "").lower()
        return "t5" in name or "flan" in name

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
                    if not self._client:
                        break
                    if self._is_text2text(m):
                        # Use text2text-generation for seq2seq models like FLAN-T5
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
                            timeout=self.timeout,
                        )
                        # Possible shapes: list[{'generated_text': str}] or dict
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
                    else:
                        out = self._client.text_generation(
                            prompt,
                            model=m,
                            max_new_tokens=max_new_tokens,
                            temperature=temperature,
                            top_p=0.9,
                            repetition_penalty=1.05,
                            timeout=self.timeout,
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

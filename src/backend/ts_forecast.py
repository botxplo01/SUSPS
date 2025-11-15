from __future__ import annotations

from typing import Any, Dict, List, Optional
import json
import os

from src.backend.advisory.hf_client import HFTextGenerator


class TimeSeriesForecaster:
    """Lightweight, free-tier-friendly time-series forecaster.

    This helper optionally calls a Hugging Face model (configured via env)
    using the same token as the advisory engine. When the model call is not
    available or fails, it falls back to a simple deterministic extrapolation.

    It treats the underlying model as a text-to-text forecaster: we send a
    compact JSON representation of the series and ask for a JSON array of
    future values. This works with general-purpose instruct models such as
    `meta-llama/Llama-3.1-8B-Instruct` and other free models, without relying
    on any paid APIs.
    """

    def __init__(self, target: str) -> None:
        self.target = target
        # Allow module-specific overrides; otherwise fall back to HF_MODEL_NAME.
        env_map = {
            "growth": "HF_GROWTH_TS_MODEL",
            "energy": "HF_ENERGY_TS_MODEL",
            "traffic": "HF_TRAFFIC_TS_MODEL",
        }
        env_name = env_map.get(target, "")
        model_override = os.getenv(env_name) if env_name else None
        # Use a slightly higher timeout than advisory by default for TS calls.
        self._gen = HFTextGenerator(model=model_override, timeout=20.0)

    # --------------------------- public API ---------------------------
    def forecast(
        self,
        series: List[Dict[str, Any]],
        horizon: int = 6,
        use_model: bool = True,
    ) -> List[Dict[str, Any]]:
        """Forecast future values for the given series.

        `series` is a list of {"t": <index or year or hour>, "value": float}.
        The result is a list of {"step": int, "t": <index>, "value": float}.

        When `use_model` is True and a HF token/model is configured, we attempt
        to call a free HF model via the shared HFTextGenerator. If that fails,
        or `use_model` is False, we fall back to a simple deterministic method.
        """

        if not series or horizon <= 0:
            return []

        if use_model and os.getenv("HF_API_KEY"):
            try:
                out = self._forecast_with_model(series, horizon)
                if out:
                    return out
            except Exception:
                # Fall through to deterministic fallback
                pass

        return self._forecast_deterministic(series, horizon)

    # ---------------------- model-backed forecast ----------------------
    def _forecast_with_model(
        self, series: List[Dict[str, Any]], horizon: int
    ) -> Optional[List[Dict[str, Any]]]:
        # Keep only minimal numeric info to control prompt size
        compact = [
            {"t": s.get("t"), "value": float(s.get("value", 0.0))} for s in series[-64:]
        ]
        prompt = (
            "You are a time-series forecasting model for urban analytics. "
            f"Target: {self.target}. "
            "Given the historical series below as JSON, forecast the next "
            f"{horizon} future steps. Use a reasonable continuation of the "
            "trend (no wild jumps). Return ONLY a JSON array with objects of "
            'the form {"step": int, "t": number, "value": float}.\n\n'
            "Historical series (most recent last):\n" + json.dumps(compact)
        )

        text = self._gen.generate(prompt, max_new_tokens=256, temperature=0.1)
        # Attempt to extract a JSON array from the response
        try:
            start = text.find("[")
            end = text.rfind("]")
            if start == -1 or end == -1 or end <= start:
                return None
            snippet = text[start : end + 1]
            data = json.loads(snippet)
            if not isinstance(data, list):
                return None
            out: List[Dict[str, Any]] = []
            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    continue
                step = int(item.get("step", i + 1))
                t = item.get("t", len(series) + step)
                val = float(item.get("value", 0.0))
                out.append({"step": step, "t": t, "value": val})
            return out or None
        except Exception:
            return None

    # ------------------ deterministic local fallback ------------------
    def _forecast_deterministic(
        self, series: List[Dict[str, Any]], horizon: int
    ) -> List[Dict[str, Any]]:
        # Simple linear extrapolation based on the last two points.
        try:
            if len(series) < 2:
                last = series[-1]
                last_t = float(last.get("t", len(series)))
                last_v = float(last.get("value", 0.0))
                return [
                    {
                        "step": i + 1,
                        "t": last_t + (i + 1),
                        "value": last_v,
                        "source": "deterministic",
                    }
                    for i in range(horizon)
                ]

            s0 = series[-2]
            s1 = series[-1]
            t0 = float(s0.get("t", len(series) - 1))
            t1 = float(s1.get("t", len(series)))
            v0 = float(s0.get("value", 0.0))
            v1 = float(s1.get("value", 0.0))
            dt = max(t1 - t0, 1.0)
            slope = (v1 - v0) / dt
        except Exception:
            # Fallback: constant extension of last value
            last = series[-1]
            last_t = float(last.get("t", len(series)))
            last_v = float(last.get("value", 0.0))
            return [
                {
                    "step": i + 1,
                    "t": last_t + (i + 1),
                    "value": last_v,
                    "source": "deterministic",
                }
                for i in range(horizon)
            ]

        out: List[Dict[str, Any]] = []
        current_t = t1
        current_v = v1
        for i in range(horizon):
            current_t = current_t + dt
            current_v = current_v + slope * dt
            out.append(
                {
                    "step": i + 1,
                    "t": current_t,
                    "value": current_v,
                    "source": "deterministic",
                }
            )
        return out

import datetime as dt
from statistics import mean
from typing import Any, Dict, List, Tuple, Optional
import hashlib
import json
import logging
from .hf_client import HFTextGenerator

logger = logging.getLogger("susps.hf")

# cache: key -> (timestamp, text, model)
_CACHE: Dict[str, Tuple[float, str, Optional[str]]] = {}
_CACHE_TTL_SEC = 600.0  # 10 minutes


def _now_ts() -> float:
    import time

    return time.time()


def _cache_get(key: str) -> Tuple[float, str, Optional[str]] | None:
    item = _CACHE.get(key)
    if not item:
        return None
    ts, text, model = item
    if _now_ts() - ts > _CACHE_TTL_SEC:
        return None
    return (ts, text, model)


def _cache_set(key: str, text: str, model: Optional[str]) -> None:
    _CACHE[key] = (_now_ts(), text, model)


def _summarize_timeseries(
    points: List[Dict[str, Any]], x_key: str, y_key: str
) -> Dict[str, Any]:
    vals = [float(p.get(y_key, 0) or 0) for p in points if p.get(y_key) is not None]
    if not vals:
        return {"count": 0}
    last = vals[-1]
    prev = vals[-2] if len(vals) > 1 else vals[-1]
    change = last - prev
    pct = (change / prev * 100.0) if prev else 0.0
    peak = max(vals)
    trough = min(vals)
    avg = mean(vals)
    return {
        "count": len(vals),
        "last": last,
        "prev": prev,
        "change": change,
        "pct_change": pct,
        "peak": peak,
        "trough": trough,
        "avg": avg,
    }


def _build_prompt(
    scope: str, summaries: Dict[str, Any], zone_id: Optional[str] = None
) -> str:
    # If a zone_id is provided, mention the selected area in the header
    context_line = f" Focus specifically on area/zone: {zone_id}." if zone_id else ""
    header = (
        "You are an urban analytics advisor embedded in the Smart Urban Simulation and Prediction System (SUSPS).\n"
        f"Given forecast outputs below{context_line}, analyze trends and provide realistic, actionable, and context-aware advice.\n"
        "Return concise insights followed by a prioritized action plan (short-term, medium-term).\n\n"
    )
    sections: List[str] = []
    for name, summ in summaries.items():
        if not isinstance(summ, dict):
            continue
        parts = [
            f"- metric: {name}",
            f"  last: {summ.get('last')}",
            f"  change_vs_prev: {summ.get('change')}",
            f"  pct_change: {round(summ.get('pct_change', 0.0), 2)}%",
            f"  avg: {round(summ.get('avg', 0.0), 2)}",
            f"  peak: {round(summ.get('peak', 0.0), 2)}",
            f"  trough: {round(summ.get('trough', 0.0), 2)}",
        ]
        sections.append("\n".join(parts))
    body = "\n\n".join(sections)
    tail = (
        "\n\nWrite the response in markdown with sections: 'Insights' and 'Recommended actions'. "
        "Prefer concrete thresholds (e.g., >15% change) and city-operations language (signals, headways, demand response)."
    )
    return f"[SCOPE={scope}]\n\n{header}{body}{tail}"


def _prepare_scope_data(scope: str, bundles: Dict[str, Any]) -> Dict[str, Any]:
    # bundles contains lists from existing endpoints
    out: Dict[str, Any] = {}
    if scope in ("dashboard", "energy") and bundles.get("energy"):
        items = bundles["energy"]
        # Choose predicted or demand depending on shape
        if items and ("predicted" in items[0] or "actual" in items[0]):
            xs = [p.get("ts") for p in items]
            pred = [
                {"x": xs[i], "y": items[i].get("predicted")} for i in range(len(items))
            ]
            out["energy_predicted"] = _summarize_timeseries(pred, "x", "y")
            if any(p.get("actual") is not None for p in items):
                act = [
                    {"x": xs[i], "y": items[i].get("actual")} for i in range(len(items))
                ]
                out["energy_actual"] = _summarize_timeseries(act, "x", "y")
        else:
            pred = [{"x": p.get("hour"), "y": p.get("demand_mwh")} for p in items]
            out["energy_profile"] = _summarize_timeseries(pred, "x", "y")

    if scope in ("dashboard", "traffic") and bundles.get("traffic"):
        items = bundles["traffic"]
        if items and ("predicted_volume" in items[0] or "actual_volume" in items[0]):
            xs = [p.get("ts") for p in items]
            pred = [
                {"x": xs[i], "y": items[i].get("predicted_volume")}
                for i in range(len(items))
            ]
            out["traffic_predicted_volume"] = _summarize_timeseries(pred, "x", "y")
            if any(p.get("actual_volume") is not None for p in items):
                act = [
                    {"x": xs[i], "y": items[i].get("actual_volume")}
                    for i in range(len(items))
                ]
                out["traffic_actual_volume"] = _summarize_timeseries(act, "x", "y")
        else:
            pred = [{"x": p.get("hour"), "y": p.get("volume")} for p in items]
            out["traffic_profile"] = _summarize_timeseries(pred, "x", "y")

    if scope in ("dashboard", "growth") and bundles.get("growth"):
        items = bundles["growth"]
        pred = [{"x": p.get("year"), "y": p.get("predicted_population")} for p in items]
        out["growth_population"] = _summarize_timeseries(pred, "x", "y")

    return out


def generate_insights_from_scope(
    scope: str, bundles: Dict[str, Any], zone_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    scope: one of 'dashboard', 'growth', 'energy', 'traffic'
    bundles: dict with any of keys 'growth', 'energy', 'traffic' as lists of items from endpoints
    zone_id: optional selected area ID that the advisory should focus on (passed through to prompt)
    returns: {"text": markdown_text, "model": model_name, "cached": bool}
    """
    scope = (scope or "dashboard").lower()
    scope = (
        scope if scope in {"dashboard", "growth", "energy", "traffic"} else "dashboard"
    )
    summary = _prepare_scope_data(scope, bundles)
    prompt = _build_prompt(scope, summary, zone_id=zone_id)
    # stable cache key (sha256 of sorted JSON, including zone for context)
    summary_with_zone = {"zone_id": zone_id, "data": summary}
    summary_json = json.dumps(summary_with_zone, sort_keys=True, default=str)
    cache_key = (
        f"advisory:{scope}:{hashlib.sha256(summary_json.encode('utf-8')).hexdigest()}"
    )
    cached = _cache_get(cache_key)
    if cached:
        ts, text, model = cached
        return {
            "text": text,
            "model": model,
            "cached": True,
            "generated_at": dt.datetime.utcfromtimestamp(ts).isoformat() + "Z",
            "fallback": False,
        }

    gen = HFTextGenerator()
    text = gen.generate(prompt)
    # Use timezone-aware UTC timestamp to avoid utcnow deprecation
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    # Detect HF fallback string and avoid caching it
    is_fallback = text.strip().startswith("Advisory engine is temporarily unavailable;")
    if is_fallback:
        try:
            logger.warning(
                "Advisory fallback used (scope=%s, model=%s). Consider increasing HF_TIMEOUT or checking token/model access.",
                scope,
                gen.model,
            )
        except Exception:
            pass
    else:
        _cache_set(cache_key, text, gen.model)
    return {
        "text": text,
        "model": gen.model,
        "cached": False,
        "generated_at": now_iso,
        "fallback": is_fallback,
    }

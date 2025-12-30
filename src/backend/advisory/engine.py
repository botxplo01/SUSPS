"""Advisory engine for the SUSPS backend.

Builds compact summaries of model outputs and processed artifacts, then
uses the Hugging Face text generator to produce cached advisory insights
for dashboard and domain-specific scopes.
"""

# @author: Lameck David Musumpuka

import datetime as dt
from statistics import mean
from typing import Any, Dict, List, Tuple, Optional
import hashlib
import json
import logging
from .hf_client import HFTextGenerator

logger = logging.getLogger("susps.hf")

# Cache: key -> (timestamp, text, model)
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
    scope: str,
    summaries: Dict[str, Any],
    zone_id: Optional[str] = None,
    scenario: Optional[str] = None,
    view: Optional[str] = None,
) -> str:
    # Include optional context (selected area, scenario, view) in the prompt header.
    context_parts: list[str] = []
    if zone_id:
        context_parts.append(f"area/zone: {zone_id}")
    if scenario:
        context_parts.append(f"scenario: {scenario}")
    if view:
        context_parts.append(f"view: {view}")
    context_line = ""
    if context_parts:
        context_line = " (" + ", ".join(context_parts) + ")"
    header = (
        "You are an urban analytics advisor embedded in the Smart Urban Simulation and Prediction System (SUSPS).\n"
        f"Given the current outputs below{context_line}, analyze trends and provide realistic, actionable, and context-aware advice.\n"
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
        # Include optional enriched fields when present.
        extra_keys = [
            "pollution_index_avg",
            "matatu_routes",
            "osm_features",
            "osm_total_km",
            "top_admin_units",
            "avg_vs_real_pct",
            "peak_vs_real_pct",
            "trough_vs_real_pct",
            "last_vs_real_pct",
        ]
        for ek in extra_keys:
            if ek in summ:
                parts.append(f"  {ek}: {summ.get(ek)}")
        sections.append("\n".join(parts))
    body = "\n\n".join(sections)
    tail = (
        "\n\nWrite the response in markdown with sections: 'Insights' and 'Recommended actions'. "
        "Prefer concrete thresholds (e.g., >15% change) and city-operations language (signals, headways, demand response)."
    )
    return f"[SCOPE={scope}]\n\n{header}{body}{tail}"


def _prepare_scope_data(scope: str, bundles: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if scope in ("dashboard", "energy") and bundles.get("energy"):
        items = bundles["energy"]
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

    # Add cross-domain context from processed artifacts when available.
    try:
        import pandas as pd
        from src.pipeline import config as _cfg

        base_dir = _cfg.PROCESSED_DIR

        # Environment + AQ (monthly) -> Temp for Energy, Pollution for Growth
        env_aq_path = base_dir / "environment_aq_features.csv"
        if env_aq_path.exists():
            env_df = pd.read_csv(env_aq_path)
            if scope in ("dashboard", "energy"):
                if "temp_c" in env_df.columns:
                    pts = [
                        {"x": int(m), "y": float(v)}
                        for m, v in zip(env_df["month"], env_df["temp_c"])
                        if pd.notna(v)
                    ]
                    if pts:
                        out["environment_temperature"] = _summarize_timeseries(
                            pts, "x", "y"
                        )
            if scope in ("dashboard", "growth"):
                if "pollution_index" in env_df.columns:
                    pts = [
                        {"x": int(m), "y": float(v)}
                        for m, v in zip(env_df["month"], env_df["pollution_index"])
                        if pd.notna(v)
                    ]
                    if pts:
                        summary = _summarize_timeseries(pts, "x", "y")
                        summary["pollution_index_avg"] = float(
                            env_df["pollution_index"].mean()
                        )
                        out["environment_pollution"] = summary

        # Enriched Traffic -> for Traffic and Growth scopes
        traf_path = base_dir / "traffic_enriched_features.csv"
        if traf_path.exists() and scope in ("dashboard", "traffic", "growth"):
            tf = pd.read_csv(traf_path)
            if "veh_per_hour" in tf.columns:
                pts = [
                    {"x": int(h), "y": float(v)}
                    for h, v in zip(tf["hour"], tf["veh_per_hour"])
                    if pd.notna(v)
                ]
                if pts:
                    ts = _summarize_timeseries(pts, "x", "y")
                    if "matatu_route_count" in tf.columns:
                        ts["matatu_routes"] = float(tf["matatu_route_count"].iloc[0])
                    if "osm_total_km" in tf.columns:
                        ts["osm_total_km"] = float(tf["osm_total_km"].iloc[0])
                    out["traffic_enriched"] = ts

        # Hotspots -> for Growth, Energy, and Traffic scopes
        hs_path = base_dir / "hotspots_areas.csv"
        if hs_path.exists() and scope in ("dashboard", "growth", "energy", "traffic"):
            hs_df = pd.read_csv(hs_path)
            if "hotspot_score" in hs_df.columns:
                scores = [
                    {"x": int(i), "y": float(v)}
                    for i, v in enumerate(hs_df["hotspot_score"])
                    if pd.notna(v)
                ]
                if scores:
                    hs_summary = _summarize_timeseries(scores, "x", "y")
                    if "admin_unit" in hs_df.columns:
                        top = (
                            hs_df.sort_values("hotspot_score", ascending=False)
                            .head(3)["admin_unit"]
                            .tolist()
                        )
                        if top:
                            hs_summary["top_admin_units"] = ", ".join(sorted(top))
                    out["urban_hotspots"] = hs_summary
    except Exception:
        # Enrichment is optional and must not break advisory generation.
        pass

    return out


def generate_insights_from_scope(
    scope: str,
    bundles: Dict[str, Any],
    zone_id: Optional[str] = None,
    scenario: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate cached advisory text from backend series bundles.

    Args:
        scope: One of 'dashboard', 'growth', 'energy', 'traffic'.
        bundles: Dict containing any of: 'growth', 'energy', 'traffic'. Values are
            the corresponding items returned by the API endpoints.
        zone_id: Optional area identifier to anchor the guidance.
        scenario: Optional scenario label to include in the prompt.

    Returns:
        Dict with: text, model, cached, generated_at, fallback.
    """
    scope = (scope or "dashboard").lower()
    scope = (
        scope if scope in {"dashboard", "growth", "energy", "traffic"} else "dashboard"
    )
    summary = _prepare_scope_data(scope, bundles)
    prompt = _build_prompt(scope, summary, zone_id=zone_id, scenario=scenario, view=None)
    # Stable cache key (sha256 of sorted JSON), including zone/scenario for context.
    summary_with_zone = {"zone_id": zone_id, "scenario": scenario, "data": summary}
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
    # Detect fallback output and avoid caching it.
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


def _prepare_snapshot_data(scope: str, snapshot: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    series = snapshot.get("series") if isinstance(snapshot, dict) else None
    if not isinstance(series, list):
        return out

    # Grouped by metric for optional baseline comparisons.
    grouped: Dict[str, Dict[str, Dict[str, Any]]] = {}

    for s in series:
        if not isinstance(s, dict):
            continue
        metric = str(s.get("metric") or "").strip().lower()
        label = str(s.get("label") or "").strip() or "series"
        pts = s.get("points")
        if not metric or not isinstance(pts, list):
            continue

        if scope != "dashboard" and metric != scope:
            continue

        norm_pts: List[Dict[str, Any]] = []
        for p in pts:
            if not isinstance(p, dict):
                continue
            try:
                x = p.get("x")
                y = p.get("y")
                if y is None:
                    continue
                norm_pts.append({"x": x, "y": float(y)})
            except Exception:
                continue

        summ = _summarize_timeseries(norm_pts, "x", "y")
        key = f"{metric}_{label}".strip().lower().replace(" ", "_")
        out[key] = summ
        grouped.setdefault(metric, {})[label.strip().lower()] = summ

    # Add comparisons to baseline/real when present.
    for metric, by_label in grouped.items():
        real = None
        for k in ("real", "baseline"):
            if k in by_label and isinstance(by_label[k], dict) and by_label[k].get("count"):
                real = by_label[k]
                break
        if not real:
            continue
        real_avg = float(real.get("avg") or 0.0)
        real_peak = float(real.get("peak") or 0.0)
        real_trough = float(real.get("trough") or 0.0)
        real_last = float(real.get("last") or 0.0)

        for lbl, summ in by_label.items():
            if lbl in ("real", "baseline"):
                continue
            if not isinstance(summ, dict) or not summ.get("count"):
                continue
            try:
                avg = float(summ.get("avg") or 0.0)
                peak = float(summ.get("peak") or 0.0)
                trough = float(summ.get("trough") or 0.0)
                last = float(summ.get("last") or 0.0)
            except Exception:
                continue

            def _pct(v: float, base: float) -> float:
                denom = base if abs(base) > 1e-6 else 1.0
                return (v - base) / denom * 100.0

            summ["avg_vs_real_pct"] = round(_pct(avg, real_avg), 2)
            summ["peak_vs_real_pct"] = round(_pct(peak, real_peak), 2)
            summ["trough_vs_real_pct"] = round(_pct(trough, real_trough), 2)
            summ["last_vs_real_pct"] = round(_pct(last, real_last), 2)

    return out


def generate_insights_from_snapshot(
    scope: str,
    snapshot: Dict[str, Any],
    zone_id: Optional[str] = None,
    scenario: Optional[str] = None,
) -> Dict[str, Any]:
    scope = (scope or "dashboard").lower()
    scope = (
        scope if scope in {"dashboard", "growth", "energy", "traffic"} else "dashboard"
    )
    view = None
    if isinstance(snapshot, dict):
        raw_view = snapshot.get("active_view")
        if raw_view is not None:
            view = str(raw_view)

    summary = _prepare_snapshot_data(scope, snapshot)
    prompt = _build_prompt(scope, summary, zone_id=zone_id, scenario=scenario, view=view)

    # Cache key includes snapshot payload so insights track the displayed data.
    cache_payload = {
        "zone_id": zone_id,
        "scenario": scenario,
        "view": view,
        "snapshot": snapshot,
        "summary": summary,
    }
    cache_json = json.dumps(cache_payload, sort_keys=True, default=str)
    cache_key = (
        f"advisory_snapshot:{scope}:{hashlib.sha256(cache_json.encode('utf-8')).hexdigest()}"
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
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    is_fallback = text.strip().startswith("Advisory engine is temporarily unavailable;")
    if not is_fallback:
        _cache_set(cache_key, text, gen.model)

    return {
        "text": text,
        "model": gen.model,
        "cached": False,
        "generated_at": now_iso,
        "fallback": is_fallback,
    }


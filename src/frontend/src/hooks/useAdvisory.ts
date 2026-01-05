/** @author: David Lameck **/

import { useEffect, useState } from "react";
import { fetchJson, postJson } from "../api";
import type { ChartPoint } from "../types";

export type AdvisoryScope = "dashboard" | "growth" | "energy" | "traffic";

export type AdvisoryMetric = "growth" | "energy" | "traffic";

export interface AdvisorySnapshotSeries {
  metric: AdvisoryMetric;
  label: string;
  points: ChartPoint[];
}

export interface AdvisorySnapshotPayload {
  active_view?: string | null;
  series: AdvisorySnapshotSeries[];
}

interface AdvisoryResponse {
  scope: string;
  zone_id?: string | null;
  scenario?: string | null;
  insights: string;
  model?: string | null;
  cached?: boolean;
  generated_at?: string | null;
  fallback?: boolean;
}

interface UseAdvisoryResult {
  insights: string | null;
  loading: boolean;
  error: string | null;
  meta: Omit<AdvisoryResponse, "insights"> | null;
}

/**
 * Fetch AI advisory text for a given scope/zone/scenario combination.
 *
 * Automatically clears state when no zone is selected and exposes both
 * the raw advisory markdown and metadata (model, cache status, etc.).
 */
export function useAdvisory(
  scope: AdvisoryScope,
  zoneId: string | null,
  scenario?: string | null,
  snapshot?: AdvisorySnapshotPayload | null,
): UseAdvisoryResult {
  const [insights, setInsights] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [meta, setMeta] = useState<Omit<AdvisoryResponse, "insights"> | null>(
    null,
  );

  useEffect(() => {
    // Do not call backend until a zone is selected
    if (!zoneId) {
      setInsights(null);
      setMeta(null);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    params.set("zone_id", zoneId);
    if (scenario) params.set("scenario", scenario);
    const qs = params.toString();
    const url = qs ? `/advisory/${scope}?${qs}` : `/advisory/${scope}`;

    const req = snapshot
      ? postJson<AdvisoryResponse>(url, snapshot)
      : fetchJson<AdvisoryResponse>(`/advisory/${scope}`, {
          zone_id: zoneId,
          scenario: scenario ?? undefined,
        });

    req
      .then((data) => {
        if (cancelled) return;
        setInsights(data.insights ?? "");
        const { insights: _text, ...rest } = data;
        setMeta(rest);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load advisory.");
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [scope, zoneId, scenario, snapshot]);

  return { insights, loading, error, meta };
}


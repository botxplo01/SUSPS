import { useEffect, useState } from "react";
import { fetchJson } from "../api";

export type AdvisoryScope = "dashboard" | "growth" | "energy" | "traffic";

interface AdvisoryResponse {
  scope: string;
  zone_id?: string | null;
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

export function useAdvisory(
  scope: AdvisoryScope,
  zoneId: string | null,
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

    fetchJson<AdvisoryResponse>(`/advisory/${scope}`, {
      zone_id: zoneId,
    })
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
  }, [scope, zoneId]);

  return { insights, loading, error, meta };
}

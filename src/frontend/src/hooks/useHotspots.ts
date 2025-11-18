import { useEffect, useState } from "react";
import { fetchJson } from "../api";
import type { HotspotArea, HotspotForecastArea } from "../types";

interface HotspotResult<T> {
  items: T[];
  loading: boolean;
  error: string | null;
}

export function useHotspotAreas(
  zoneId?: string | null,
): HotspotResult<HotspotArea> {
  const [items, setItems] = useState<HotspotArea[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const params = zoneId ? { zone_id: zoneId } : undefined;
    fetchJson<{ items: any[] }>("/hotspots/areas", params)
      .then((data) => {
        if (cancelled) return;
        const raw = data.items ?? [];
        const mapped: HotspotArea[] = raw.map((r) => ({
          admin_unit: String(r.admin_unit ?? "Area"),
          population:
            typeof r.population === "number" ? r.population : undefined,
          pop_share:
            typeof r.pop_share === "number" ? r.pop_share : undefined,
          income_norm:
            typeof r.income_norm === "number" ? r.income_norm : undefined,
          employment_score:
            typeof r.employment_score === "number"
              ? r.employment_score
              : undefined,
          hotspot_score:
            typeof r.hotspot_score === "number" ? r.hotspot_score : undefined,
        }));
        setItems(mapped);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof Error ? err.message : "Failed to load hotspots.",
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [zoneId]);

  return { items, loading, error };
}

export function useHotspotForecast(
  year?: number,
  zoneId?: string | null,
): HotspotResult<HotspotForecastArea> {
  const [items, setItems] = useState<HotspotForecastArea[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    const params = {
      ...(year != null ? { year } : {}),
      ...(zoneId ? { zone_id: zoneId } : {}),
    };
    fetchJson<{ items: any[] }>("/hotspots/areas/forecast", params)
      .then((data) => {
        if (cancelled) return;
        const raw = data.items ?? [];
        const mapped: HotspotForecastArea[] = raw.map((r) => ({
          admin_unit: String(r.admin_unit ?? "Area"),
          year: Number(r.year ?? 0),
          population:
            typeof r.population === "number" ? r.population : undefined,
          pop_share:
            typeof r.pop_share === "number" ? r.pop_share : undefined,
          income_norm:
            typeof r.income_norm === "number" ? r.income_norm : undefined,
          employment_score:
            typeof r.employment_score === "number"
              ? r.employment_score
              : undefined,
          hotspot_score:
            typeof r.hotspot_score === "number" ? r.hotspot_score : undefined,
        }));
        setItems(mapped);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof Error ? err.message : "Failed to load hotspot forecast.",
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [year, zoneId]);

  return { items, loading, error };
}

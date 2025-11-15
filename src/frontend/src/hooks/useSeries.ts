import { useEffect, useState } from "react";
import { fetchJson } from "../api";
import type { ChartPoint } from "../types";

interface SeriesResult {
  points: ChartPoint[];
  loading: boolean;
  error: string | null;
}

export function useGrowthSeries(areaId: number | null): SeriesResult {
  const [points, setPoints] = useState<ChartPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (areaId == null) {
      setPoints([]);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchJson<{ items: any[] }>("/growth", { area_id: areaId })
      .then((data) => {
        if (cancelled) return;
        const items = data.items ?? [];
        const mapped: ChartPoint[] = items
          .map((it) => ({
            x: Number(it.year ?? 0),
            y: Number(it.predicted_population ?? 0),
          }))
          .filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y));
        setPoints(mapped);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load growth.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [areaId]);

  return { points, loading, error };
}

export function useEnergySeries(areaId: number | null): SeriesResult {
  const [points, setPoints] = useState<ChartPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (areaId == null) {
      setPoints([]);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchJson<{ items: any[] }>("/energy", { area_id: areaId })
      .then((data) => {
        if (cancelled) return;
        const items = data.items ?? [];
        let mapped: ChartPoint[] = [];
        if (items[0] && ("predicted" in items[0] || "actual" in items[0])) {
          mapped = items
            .map((it, idx) => ({
              x: idx,
              y: Number(it.predicted ?? it.actual ?? 0),
            }))
            .filter((p) => Number.isFinite(p.y));
        } else {
          mapped = items
            .map((it) => ({
              x: Number(it.hour ?? 0),
              y: Number(it.demand_mwh ?? 0),
            }))
            .filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y));
        }
        setPoints(mapped);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load energy.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [areaId]);

  return { points, loading, error };
}

export function useTrafficSeries(areaId: number | null): SeriesResult {
  const [points, setPoints] = useState<ChartPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (areaId == null) {
      setPoints([]);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchJson<{ items: any[] }>("/traffic", { area_id: areaId })
      .then((data) => {
        if (cancelled) return;
        const items = data.items ?? [];
        let mapped: ChartPoint[] = [];
        if (
          items[0] &&
          ("predicted_volume" in items[0] || "actual_volume" in items[0])
        ) {
          mapped = items
            .map((it, idx) => ({
              x: idx,
              y: Number(it.predicted_volume ?? it.actual_volume ?? 0),
            }))
            .filter((p) => Number.isFinite(p.y));
        } else {
          mapped = items
            .map((it) => ({
              x: Number(it.hour ?? 0),
              y: Number(it.volume ?? 0),
            }))
            .filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y));
        }
        setPoints(mapped);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load traffic.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [areaId]);

  return { points, loading, error };
}

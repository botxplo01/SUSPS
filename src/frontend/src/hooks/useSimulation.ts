/** @author: Lameck David Musumpuka **/

import { useEffect, useState } from "react";
import { postJson } from "../api";
import type { ChartPoint } from "../types";

type SimulationModule = "growth" | "energy" | "traffic";

interface SimulationSeriesResult {
  points: ChartPoint[];
  loading: boolean;
  error: string | null;
}

interface SimulationRunResponse {
  module: string;
  results?: Record<string, unknown>;
}

interface UseSimulationOptions {
  areaId?: number | null;
  parameters?: Record<string, unknown>;
  runKey?: number;
}

/**
 * Run a SIMULATE scenario for growth/energy/traffic and expose the
 * resulting series as ChartPoint data.
 *
 * The hook is edge-triggered by `runKey` so callers can control when a
 * new simulation should be executed.
 */
export function useSimulationSeries(
  module: SimulationModule,
  enabled: boolean,
  options?: UseSimulationOptions,
): SimulationSeriesResult {
  const { areaId, parameters, runKey = 0 } = options ?? {};
  const [points, setPoints] = useState<ChartPoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled || areaId == null || runKey === 0) {
      setPoints([]);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    postJson<SimulationRunResponse>("/simulate/run", {
      module,
      area_id: areaId,
      parameters: parameters ?? {},
    })
      .then((data) => {
        if (cancelled) return;
        const results = (data && data.results) || {};
        const items = (results as Record<string, unknown[]>)[module] ?? [];

        let mapped: ChartPoint[] = [];
        if (module === "growth") {
          mapped = (items as any[])
            .map((it) => ({
              x: Number(it.year ?? 0),
              y: Number(it.predicted_population ?? 0),
            }))
            .filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y));
        } else if (module === "energy") {
          mapped = (items as any[])
            .map((it) => ({
              x: Number(it.hour ?? 0),
              y: Number(it.demand_mwh ?? 0),
            }))
            .filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y));
        } else if (module === "traffic") {
          mapped = (items as any[])
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
        setError(
          err instanceof Error ? err.message : "Failed to run simulation.",
        );
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [module, enabled, areaId, runKey]);

  return { points, loading, error };
}


// @author: David Lameck

import { useEffect, useMemo, useRef, useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { ModeToggle } from "../components/ModeToggle";
import { DescriptionSection } from "../components/DescriptionSection";
import { Table } from "../components/Table";
import { Histogram } from "../components/Histogram";
import { HotspotMap } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { ActionToggle } from "../components/ActionToggle";
import { FormattedInsights } from "../components/FormattedInsights";
import { ExportDialog } from "../components/ExportDialog";
import { postJson, postBinary, downloadBlob, fetchJson } from "../api";
import type {
  Area,
  Mode,
  ChartPoint,
  ChartSeries,
  ExportPayload,
  ExportPage,
  ExportFormat,
  ChartExportHandle,
} from "../types";
import { useAdvisory } from "../hooks/useAdvisory";
import { useTrafficSeries } from "../hooks/useSeries";
import { useSimulationSeries } from "../hooks/useSimulation";

interface TrafficPageProps {
  selectedArea: Area | null;
  onRegisterExporter?: (fn: () => void) => void;
}

type TrafficExportTarget =
  | { kind: "page" }
  | { kind: "chart"; id: "volume" }
  | { kind: "table"; id: "volume" };

/** Footer text used for Traffic PDF/CSV exports. */
const EXPORT_FOOTER_TEXT =
  "Smart Urban Simulation and Prediction System (SUSPS) — © 2025 Developed by David Lameck.";

function getTrafficScenarioLabel(id: string): string {
  switch (id) {
    case "traffic_baseline":
      return "Baseline";
    case "traffic_remote_work":
      return "Remote work adoption";
    case "traffic_congestion_pricing":
      return "Congestion pricing";
    case "traffic_simulate":
      return "Custom simulate";
    default:
      return "Custom simulate";
  }
}

function getTrafficScenarioClass(id: string): string {
  switch (id) {
    case "traffic_baseline":
      return "bg-slate-100 text-slate-700";
    case "traffic_remote_work":
      return "bg-emerald-50 text-emerald-700";
    case "traffic_congestion_pricing":
      return "bg-amber-50 text-amber-700";
    case "traffic_simulate":
      return "bg-slate-100 text-slate-700";
    default:
      return "bg-slate-100 text-slate-700";
  }
}

function computeTrafficTrend(points: ChartPoint[]): ChartPoint[] {
  if (points.length < 2) return points.slice();
  const n = points.length;
  let sumX = 0;
  let sumY = 0;
  let sumXY = 0;
  let sumX2 = 0;
  for (const p of points) {
    const x = p.x;
    const y = p.y;
    sumX += x;
    sumY += y;
    sumXY += x * y;
    sumX2 += x * x;
  }
  const denom = n * sumX2 - sumX * sumX || 1;
  const slope = (n * sumXY - sumX * sumY) / denom;
  const intercept = sumY / n - (slope * sumX) / n;
  return points.map((p) => ({ x: p.x, y: Math.max(intercept + slope * p.x, 0) }));
}

function computeTrafficOptimal(real: ChartPoint[], sim: ChartPoint[]): ChartPoint[] {
  const len = Math.min(real.length, sim.length);
  const out: ChartPoint[] = [];
  for (let i = 0; i < len; i += 1) {
    const r = real[i];
    const s = sim[i];
    out.push({ x: r.x, y: (r.y + s.y) / 2 });
  }
  return out;
}

/**
 * Traffic module page.
 *
 * Displays baseline hourly traffic volumes plus SIMULATE scenarios and an
 * Optimize overlay, alongside a hotspot map and AI advisory for the
 * selected area.
 */
export function TrafficPage({
  selectedArea,
  onRegisterExporter,
}: TrafficPageProps) {
  const [mode, setMode] = useState<Mode>("REAL");
  const [optimize, setOptimize] = useState(false);
  const [simulateRun, setSimulateRun] = useState(0);
  const [volumeScale, setVolumeScale] = useState<number>(1.1);
  const [peakShift, setPeakShift] = useState<number>(0);
  const [peakScale, setPeakScale] = useState<number>(1.2);
  const [offpeakScale, setOffpeakScale] = useState<number>(1.0);
  const [flattenRatio, setFlattenRatio] = useState<number>(0);
  const [scenarioId, setScenarioId] = useState<string>("traffic_baseline");
  const [predictedTraffic, setPredictedTraffic] = useState<ChartPoint[]>([]);
  const [predicting, setPredicting] = useState(false);
  const [predictError, setPredictError] = useState<string | null>(null);
  const [optimalTraffic, setOptimalTraffic] = useState<ChartPoint[]>([]);
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);
  const [livePayload, setLivePayload] = useState<any | null>(null);
  const [liveLoading, setLiveLoading] = useState(false);
  const [liveError, setLiveError] = useState<string | null>(null);
  const chartRef = useRef<ChartExportHandle | null>(null);
  const liveTimerRef = useRef<number | null>(null);
  const [exportTarget, setExportTarget] = useState<TrafficExportTarget | null>(
    null,
  );
  const zoneId = selectedArea ? selectedArea.name : null;
  const scenarioLabel = getTrafficScenarioLabel(scenarioId);
  const scenarioClass = getTrafficScenarioClass(scenarioId);
  const { points: trafficPoints, loading: trafficLoading } = useTrafficSeries(
    selectedArea ? selectedArea.id : null,
  );
  const {
    points: simulateTrafficPoints,
    loading: simulateTrafficLoading,
    error: simulateTrafficError,
  } = useSimulationSeries(
    "traffic",
    !!selectedArea && mode === "SIMULATE",
    {
      areaId: selectedArea?.id ?? null,
      parameters: {
        volume_scale: volumeScale,
        peak_hour_shift: peakShift,
        peak_scale: peakScale,
        offpeak_scale: offpeakScale,
        flatten_ratio: flattenRatio,
      },
      runKey: simulateRun,
    },
  );
  const basePoints = trafficPoints;

  const advisorySnapshot = useMemo(() => {
    const series: { metric: "traffic"; label: string; points: ChartPoint[] }[] = [];

    if (basePoints.length) {
      series.push({ metric: "traffic", label: "Real", points: basePoints });
    }
    if (
      mode === "REAL" &&
      predictedTraffic.length === basePoints.length &&
      predictedTraffic.length
    ) {
      series.push({
        metric: "traffic",
        label: "Predicted",
        points: predictedTraffic,
      });
    }
    if (
      mode === "SIMULATE" &&
      simulateRun > 0 &&
      simulateTrafficPoints.length === basePoints.length
    ) {
      series.push({
        metric: "traffic",
        label: "Simulated",
        points: simulateTrafficPoints,
      });
    }
    if (optimize && optimalTraffic.length === basePoints.length && optimalTraffic.length) {
      series.push({ metric: "traffic", label: "Optimal", points: optimalTraffic });
    }

    return {
      active_view: mode,
      series,
    };
  }, [
    basePoints,
    mode,
    predictedTraffic,
    simulateRun,
    simulateTrafficPoints,
    optimize,
    optimalTraffic,
  ]);

  const { insights, loading, error } = useAdvisory(
    "traffic",
    zoneId,
    scenarioId,
    advisorySnapshot,
  );

  useEffect(() => {
    if (!onRegisterExporter) return;
    onRegisterExporter(() => {
      setExportTarget({ kind: "page" });
      setIsExportDialogOpen(true);
    });
  }, [onRegisterExporter]);

  useEffect(() => {
    // Manual refresh only for live traffic (credit-friendly). Keep the last
    // loaded payload until the user explicitly clicks Refresh.
    return () => {
      if (liveTimerRef.current != null) {
        window.clearInterval(liveTimerRef.current);
        liveTimerRef.current = null;
      }
    };
  }, []);

  const runTrafficForecast = async () => {
    setMode("REAL");
    setOptimize(false);
    setSimulateRun(0);
    setPredictError(null);

    if (!basePoints.length) {
      setPredictedTraffic([]);
      return;
    }

    setPredicting(true);
    try {
      const seriesPayload = basePoints.map((p) => ({ t: p.x, value: p.y }));
      const data = await postJson<{
        target: string;
        items: { step: number; t: number; value: number }[];
        used_model?: boolean;
      }>("/ts/forecast", {
        target: "traffic",
        series: seriesPayload,
        horizon: seriesPayload.length,
        use_model: true,
      });
      const items = data.items ?? [];
      if (items.length) {
        const trimmed = items.slice(0, basePoints.length);
        const mapped: ChartPoint[] = trimmed.map((it, idx) => ({
          x: basePoints[idx].x,
          y: Number(it.value ?? 0),
        }));
        setPredictedTraffic(mapped);
      } else {
        setPredictedTraffic(computeTrafficTrend(basePoints));
      }
    } catch (err) {
      setPredictError(
        err instanceof Error ? err.message : "Failed to compute forecast.",
      );
      setPredictedTraffic(computeTrafficTrend(basePoints));
    } finally {
      setPredicting(false);
    }
  };

  const handlePredictClick = () => {
    void runTrafficForecast();
  };

  useEffect(() => {
    if (mode === "SIMULATE" && optimize && basePoints.length && simulateTrafficPoints.length) {
      setOptimalTraffic(computeTrafficOptimal(basePoints, simulateTrafficPoints));
    }
    if (!optimize) {
      setOptimalTraffic([]);
    }
  }, [mode, optimize, basePoints, simulateTrafficPoints]);

  const trafficSeries: ChartSeries[] = [];
  if (basePoints.length) {
    trafficSeries.push({ label: "Real", color: "#f24152", points: basePoints });
  }
  if (mode === "REAL" && predictedTraffic.length === basePoints.length && predictedTraffic.length) {
    trafficSeries.push({ label: "Predicted", color: "#de3388", points: predictedTraffic });
  }
  if (mode === "SIMULATE" && simulateRun > 0 && simulateTrafficPoints.length === basePoints.length) {
    trafficSeries.push({ label: "Simulated", color: "#1b55ce", points: simulateTrafficPoints });
  }
  if (optimize && optimalTraffic.length === basePoints.length && optimalTraffic.length) {
    trafficSeries.push({ label: "Optimal", color: "#08c44d", points: optimalTraffic });
  }

  const handleOpenFullExport = () => {
    setExportTarget({ kind: "page" });
    setIsExportDialogOpen(true);
  };

  const handleOpenTableExport = () => {
    setExportTarget({ kind: "table", id: "volume" });
    setIsExportDialogOpen(true);
  };

  const handleOpenChartExport = () => {
    setExportTarget({ kind: "chart", id: "volume" });
    setIsExportDialogOpen(true);
  };

  const buildExportPage = (
    target: TrafficExportTarget,
    chartImage?: string | null,
  ): ExportPage => {
    const areaName = selectedArea?.name ?? "No area selected";
    const description = selectedArea
      ? `Traffic module for ${selectedArea.name} in ${mode} mode.`
      : "Traffic module showing baseline hourly volume profile.";
    const insightsText =
      selectedArea && !loading && !error && insights ? insights : undefined;

    const tables =
      target.kind === "chart"
        ? []
        : [
            {
              title: "Hourly traffic volume",
              columns: ["Hour", "Volume (veh/hr)"],
              rows:
                basePoints && basePoints.length
                  ? basePoints.map((p) => [
                      String(p.x),
                      Math.round(p.y).toString(),
                    ])
                  : [["—", "—"]],
            },
          ];

    const charts =
      target.kind === "table"
        ? []
        : [
            {
              title: "Traffic Volume",
              x_label: "Hour of day",
              y_label: "Volume (veh/hr)",
              series: trafficSeries.map((s) => ({
                label: s.label,
                points: s.points,
              })),
              image_data: chartImage ?? undefined,
            },
          ];

    return {
      page_name: "Traffic",
      mode,
      area_name: areaName,
      area_id: selectedArea?.id ?? null,
      description,
      insights: insightsText,
      tables,
      charts,
    };
  };

  const handleConfirmExport = async (format: ExportFormat) => {
    if (!exportTarget) return;
    const chartImage = chartRef.current ? await chartRef.current.capturePng() : null;
    const page = buildExportPage(exportTarget, chartImage);
    const payload: ExportPayload = {
      export_format: format,
      pages: [page],
      footer_text: EXPORT_FOOTER_TEXT,
    };

    try {
      const blob = await postBinary("/export", payload);
      const areaNameFragment = selectedArea?.name
        ? ` - ${selectedArea.name}`
        : "";
      const baseName =
        exportTarget.kind === "page"
          ? `SUSPS - Traffic${areaNameFragment}`
          : exportTarget.kind === "table"
          ? `SUSPS - Traffic - Volume table${areaNameFragment}`
          : `SUSPS - Traffic - Volume chart${areaNameFragment}`;
      const ext = format === "pdf" ? ".pdf" : format === "csv" ? ".csv" : ".zip";
      downloadBlob(blob, `${baseName}${ext}`);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("Failed to export Traffic data", err);
    }
  };

  return (
    <div className="space-y-4 pb-16">
      <div className="flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-center">
        <AreaBadge name={selectedArea?.name ?? "No area selected"} />
        <div className="flex items-center gap-3">
          {selectedArea && (
            <span
              className={`rounded-full px-3 py-1 text-xs font-medium ${scenarioClass}`}
            >
              Scenario: {scenarioLabel}
            </span>
          )}
          <ModeToggle
            mode={mode}
            onChange={(next) => {
              setMode(next);
              setOptimize(false);
              if (next === "REAL") {
                setSimulateRun(0);
                setScenarioId("traffic_baseline");
              } else {
                setScenarioId((prev) =>
                  prev === "traffic_baseline" ? "traffic_simulate" : prev,
                );
              }
            }}
          />
        </div>
      </div>

      <DescriptionSection title="Traffic Flow Overview">
        {selectedArea ? (
          <>
            In REAL mode, the table and histogram show the baseline hourly traffic
            volumes for {selectedArea.name}: each row and bar corresponds to one
            hour of a representative day and reflects the modeled number of
            vehicles per hour on key links. The hotspot map highlights where these
            volumes translate into higher congestion risk.
            <br />
            In SIMULATE mode, the same hourly structure is preserved but the
            volumes are transformed by your scenario parameters: overall volume
            scaling, peak-hour shifts, different multipliers for peak vs off-peak
            periods, and optional flattening toward the average. This helps you
            reason about policies like remote work adoption, congestion pricing, or
            modal shifts relative to the baseline flow pattern.
          </>
        ) : (
          <>
            Select an area from the sidebar to view its baseline hourly traffic
            volumes and congestion hotspots in REAL mode. Once an area is selected,
            you can switch to SIMULATE to explore how demand-management or routing
            policies might reshape the hourly volume profile.
          </>
        )}
      </DescriptionSection>

      <section className="rounded-xl bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 className="flex items-center gap-2 text-sm font-semibold text-red-600">
              <span className="inline-block h-2 w-2 rounded-full bg-red-600" />
              Live traffic
            </h2>
            <p className="mt-1 text-xs text-gray-600">
              TomTom flow snapshot near {selectedArea?.name ?? "your city"}.
            </p>
            {livePayload?.meta && (
              <p className="mt-1 text-[11px] text-gray-500">
                Updated{" "}
                {typeof livePayload.meta.served_at === "string"
                  ? livePayload.meta.served_at
                  : typeof livePayload.meta.generated_at === "string"
                    ? livePayload.meta.generated_at
                    : "—"}
                {typeof livePayload.meta.cached === "boolean"
                  ? ` (cached: ${livePayload.meta.cached ? "yes" : "no"})`
                  : ""}
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={() => {
              setLiveLoading(true);
              setLiveError(null);
              fetchJson<any>("/traffic/live", { fresh: 1 })
                .then((data) => setLivePayload(data))
                .catch((err: unknown) => {
                  setLivePayload(null);
                  setLiveError(
                    err instanceof Error
                      ? err.message
                      : "Live traffic unavailable.",
                  );
                })
                .finally(() => setLiveLoading(false));
            }}
            className="rounded-md bg-neutral-900 px-3 py-2 text-xs font-medium text-white hover:bg-neutral-800"
          >
            Refresh
          </button>
        </div>

        {liveLoading && (
          <p className="mt-3 text-xs text-gray-500">Loading live traffic...</p>
        )}
        {!liveLoading && liveError && (
          <p className="mt-3 text-xs text-red-600">{liveError}</p>
        )}

        {!liveLoading && !liveError && !livePayload && (
          <p className="mt-3 text-xs text-gray-500">
            Click Refresh to fetch a live TomTom snapshot.
          </p>
        )}

        {!liveLoading && !liveError && livePayload?.meta && (
          <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-lg bg-neutral-50 p-3">
              <div className="text-[11px] font-medium text-gray-600">Congestion ratio</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">
                {typeof livePayload.meta.avg_congestion_ratio === "number"
                  ? livePayload.meta.avg_congestion_ratio.toFixed(2)
                  : "—"}
              </div>
            </div>
            <div className="rounded-lg bg-neutral-50 p-3">
              <div className="text-[11px] font-medium text-gray-600">Current speed</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">
                {typeof livePayload.meta.avg_current_speed === "number"
                  ? `${livePayload.meta.avg_current_speed.toFixed(1)} km/h`
                  : "—"}
              </div>
            </div>
            <div className="rounded-lg bg-neutral-50 p-3">
              <div className="text-[11px] font-medium text-gray-600">Free-flow speed</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">
                {typeof livePayload.meta.avg_free_flow_speed === "number"
                  ? `${livePayload.meta.avg_free_flow_speed.toFixed(1)} km/h`
                  : "—"}
              </div>
            </div>
            <div className="rounded-lg bg-neutral-50 p-3">
              <div className="text-[11px] font-medium text-gray-600">Samples</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">
                {typeof livePayload.meta.samples_used === "number"
                  ? livePayload.meta.samples_used
                  : "—"}
              </div>
            </div>
          </div>
        )}

        {!liveLoading && !liveError && Array.isArray(livePayload?.points) && (
          <div className="mt-3">
            <Table
              title="Live flow points"
              columns={["Point", "Current", "Free-flow", "Ratio", "Confidence", "Closed"]}
              rows={
                livePayload.points.length
                  ? livePayload.points.map((p: any) => [
                      String(p.id ?? "—"),
                      typeof p.current_speed === "number"
                        ? `${p.current_speed.toFixed(1)} km/h`
                        : "—",
                      typeof p.free_flow_speed === "number"
                        ? `${p.free_flow_speed.toFixed(1)} km/h`
                        : "—",
                      typeof p.congestion_ratio === "number"
                        ? p.congestion_ratio.toFixed(2)
                        : "—",
                      typeof p.confidence === "number" ? p.confidence.toFixed(2) : "—",
                      p.road_closure ? "Yes" : "No",
                    ])
                  : [["—", "—", "—", "—", "—", "—"]]
              }
            />
          </div>
        )}
      </section>

      {selectedArea && mode === "SIMULATE" && (
        <section className="rounded-xl bg-[#fffcf3] p-4 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold text-gray-800">
            Simulation parameters
          </h2>
          <div className="mb-3 flex flex-wrap gap-2 text-[11px]">
            <span className="mr-1 font-semibold text-gray-600">Presets:</span>
            <button
              type="button"
              onClick={() => {
                setMode("REAL");
                setScenarioId("traffic_baseline");
                setVolumeScale(1.0);
                setPeakShift(0);
                setPeakScale(1.0);
                setOffpeakScale(1.0);
                setFlattenRatio(0);
              }}
              className="rounded-full bg-neutral-200 px-3 py-1 text-gray-800 hover:bg-neutral-300"
            >
              Baseline
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("SIMULATE");
                setScenarioId("traffic_remote_work");
                setVolumeScale(0.85);
                setPeakShift(-1);
                setPeakScale(0.8);
                setOffpeakScale(0.9);
                setFlattenRatio(0.3);
              }}
              className="rounded-full bg-emerald-50 px-3 py-1 text-emerald-700 hover:bg-emerald-100"
            >
              Remote work adoption
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("SIMULATE");
                setScenarioId("traffic_congestion_pricing");
                setVolumeScale(0.9);
                setPeakShift(0);
                setPeakScale(0.75);
                setOffpeakScale(1.05);
                setFlattenRatio(0.4);
              }}
              className="rounded-full bg-amber-50 px-3 py-1 text-amber-700 hover:bg-amber-100"
            >
              Congestion pricing
            </button>
          </div>
          <p className="mb-3 text-xs text-gray-600">
            Adjust the traffic volume scale, peak-hours, and flattening, then
            switch to Simulate mode to see how the hourly profile changes.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Volume scale
              </label>
              <input
                type="number"
                min={0.5}
                max={2}
                step={0.1}
                value={volumeScale}
                onChange={(e) =>
                  setVolumeScale(Number(e.target.value) || 0)
                }
                className="w-full rounded-md border border-neutral-300 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-neutral-400"
              />
              <p className="mt-1 text-[11px] text-gray-500">
                1.0 = baseline; values &gt;1 increase volume, values &lt;1 decrease it.
              </p>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Peak hour shift (hours)
              </label>
              <input
                type="number"
                min={-12}
                max={12}
                step={1}
                value={peakShift}
                onChange={(e) => setPeakShift(Number(e.target.value) || 0)}
                className="w-full rounded-md border border-neutral-300 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-neutral-400"
              />
              <p className="mt-1 text-[11px] text-gray-500">
                Positive values shift peaks later in the day; negative values
                earlier (e.g. school schedule changes, remote work adoption).
              </p>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Peak vs off-peak scaling
              </label>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <input
                    type="number"
                    min={0.5}
                    max={2}
                    step={0.1}
                    value={peakScale}
                    onChange={(e) =>
                      setPeakScale(Number(e.target.value) || 0)
                    }
                    className="w-full rounded-md border border-neutral-300 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-neutral-400"
                  />
                  <p className="mt-1 text-[11px] text-gray-500">Peak hours</p>
                </div>
                <div>
                  <input
                    type="number"
                    min={0.5}
                    max={2}
                    step={0.1}
                    value={offpeakScale}
                    onChange={(e) =>
                      setOffpeakScale(Number(e.target.value) || 0)
                    }
                    className="w-full rounded-md border border-neutral-300 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-neutral-400"
                  />
                  <p className="mt-1 text-[11px] text-gray-500">Off-peak hours</p>
                </div>
              </div>
              <p className="mt-1 text-[11px] text-gray-500">
                Use to simulate congestion pricing, increased transit share, or
                targeted enforcement.
              </p>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Flattening toward average (0–1)
              </label>
              <input
                type="number"
                min={0}
                max={1}
                step={0.1}
                value={flattenRatio}
                onChange={(e) => setFlattenRatio(Number(e.target.value) || 0)}
                className="w-full rounded-md border border-neutral-300 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-neutral-400"
              />
              <p className="mt-1 text-[11px] text-gray-500">
                0 = keep current shape; values closer to 1 flatten peaks (e.g.
                strong modal shift or coordinated traffic management).
              </p>
            </div>
          </div>
        </section>
      )}

      <Table
        title="Traffic volume table"
        onExport={handleOpenTableExport}
        columns={["Hour", "Volume (veh/hr)"]}
        rows={
          selectedArea && basePoints.length > 0
            ? basePoints.map((p, idx) => {
                const real = Math.round(p.y);
                const pred =
                  mode === "REAL" && predictedTraffic[idx]
                    ? Math.round(predictedTraffic[idx].y)
                    : null;
                const sim =
                  mode === "SIMULATE" && simulateRun > 0 && simulateTrafficPoints[idx]
                    ? Math.round(simulateTrafficPoints[idx].y)
                    : null;
                const opt =
                  optimize && optimalTraffic[idx]
                    ? Math.round(optimalTraffic[idx].y)
                    : null;
                return [
                  p.x,
                  (
                    <>
                      {real.toLocaleString()}
                      {pred !== null && (
                        <span className="ml-1 text-[11px] text-[#de3388]">
                          ({pred.toLocaleString()})
                        </span>
                      )}
                      {sim !== null && (
                        <span className="ml-1 text-[11px] text-[#1b55ce]">
                          ({sim.toLocaleString()})
                        </span>
                      )}
                      {opt !== null && (
                        <span className="ml-1 text-[11px] text-[#08c44d]">
                          ({opt.toLocaleString()})
                        </span>
                      )}
                    </>
                  ),
                ];
              })
            : [["—", "—"]]
        }
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Histogram
          ref={chartRef}
          title="Traffic Volume"
          series={trafficSeries}
          xLabel="Hour of day"
          yLabel="Volume (veh/hr)"
          onExport={handleOpenChartExport}
        />
        <HotspotMap optimize={optimize} zoneId={selectedArea?.name ?? null} />
      </div>

      {selectedArea && trafficLoading && (
        <p className="text-xs text-gray-500">Loading traffic series...</p>
      )}
      {selectedArea && predicting && !trafficLoading && (
        <p className="text-xs text-gray-500">Computing forecast overlay...</p>
      )}
      {selectedArea && predictError && (
        <p className="text-xs text-red-600">{predictError}</p>
      )}
      {selectedArea && mode === "SIMULATE" && simulateTrafficLoading && (
        <p className="text-xs text-gray-500">Loading simulated traffic...</p>
      )}
      {selectedArea && mode === "SIMULATE" && simulateTrafficError && (
        <p className="text-xs text-red-600">{simulateTrafficError}</p>
      )}

      <InsightsSection>
        {!selectedArea && (
          <p>Select an area to generate detailed traffic advisory.</p>
        )}
        {selectedArea && loading && <p>Loading advisory...</p>}
        {selectedArea && error && (
          <p className="text-red-600 text-sm">{error}</p>
        )}
        {selectedArea && !loading && !error && insights && (
          <>
            <FormattedInsights text={insights} />
            {scenarioId !== "traffic_baseline" && (
              <p className="mt-2 text-[11px] text-gray-500">
                Scenario: {scenarioLabel}
              </p>
            )}
          </>
        )}
        {selectedArea && optimize && (
          <p className="mt-2 text-xs text-emerald-700">
            With Optimize active, the green optimal zones on the hotspot map
            indicate places where forecast congestion risk improves compared to
            today.
          </p>
        )}
      </InsightsSection>

      <ExportDialog
        isOpen={isExportDialogOpen}
        onClose={() => {
          setIsExportDialogOpen(false);
          setExportTarget(null);
        }}
        onConfirm={(format) => {
          void handleConfirmExport(format);
        }}
      />

      <ActionToggle
        mode={mode}
        onPredict={handlePredictClick}
        onOptimize={() => {
          setOptimize(true);
          if (mode === "SIMULATE") {
            setSimulateRun((prev) => prev + 1);
          }
        }}
        onSimulate={() => {
          if (mode === "SIMULATE") {
            setSimulateRun((prev) => prev + 1);
            setOptimize(false);
          }
        }}
      />
    </div>
  );
}

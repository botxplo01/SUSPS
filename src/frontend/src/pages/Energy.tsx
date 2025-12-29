// @author: David Lameck

import { useEffect, useMemo, useRef, useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { ModeToggle } from "../components/ModeToggle";
import { DescriptionSection } from "../components/DescriptionSection";
import { Table } from "../components/Table";
import { LineChart } from "../components/LineChart";
import { HotspotMap } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { ActionToggle } from "../components/ActionToggle";
import { FormattedInsights } from "../components/FormattedInsights";
import { ExportDialog } from "../components/ExportDialog";
import { postJson, postBinary, downloadBlob } from "../api";
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
import { useEnergySeries } from "../hooks/useSeries";
import { useSimulationSeries } from "../hooks/useSimulation";

interface EnergyPageProps {
  selectedArea: Area | null;
  onRegisterExporter?: (fn: () => void) => void;
}

type EnergyExportTarget =
  | { kind: "page" }
  | { kind: "chart"; id: "consumption" }
  | { kind: "table"; id: "demand" };

/** Footer text used for Energy PDF/CSV exports. */
const EXPORT_FOOTER_TEXT =
  "Smart Urban Simulation and Prediction System (SUSPS) — © 2025 Developed by David Lameck.";

function getEnergyScenarioLabel(id: string): string {
  switch (id) {
    case "energy_baseline":
      return "Baseline";
    case "energy_peak_spike":
      return "Evening peak spike";
    case "energy_demand_response":
      return "Demand response pilot";
    case "energy_simulate":
      return "Custom simulate";
    default:
      return "Custom simulate";
  }
}

function getEnergyScenarioClass(id: string): string {
  switch (id) {
    case "energy_baseline":
      return "bg-slate-100 text-slate-700";
    case "energy_peak_spike":
      return "bg-amber-50 text-amber-700";
    case "energy_demand_response":
      return "bg-emerald-50 text-emerald-700";
    case "energy_simulate":
      return "bg-slate-100 text-slate-700";
    default:
      return "bg-slate-100 text-slate-700";
  }
}

function computeEnergyTrend(points: ChartPoint[]): ChartPoint[] {
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

function computeEnergyOptimal(real: ChartPoint[], sim: ChartPoint[]): ChartPoint[] {
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
 * Energy module page.
 *
 * Shows baseline hourly demand, allows HF-backed/deterministic forecasts
 * in REAL mode, and SIMULATE scenarios overlaid with an optional Optimize
 * curve in SIMULATE mode.
 */
export function EnergyPage({
  selectedArea,
  onRegisterExporter,
}: EnergyPageProps) {
  const [mode, setMode] = useState<Mode>("REAL");
  const [optimize, setOptimize] = useState(false);
  const [simulateRun, setSimulateRun] = useState(0);
  const [demandScale, setDemandScale] = useState<number>(1.1);
  const [peakShift, setPeakShift] = useState<number>(0);
  const [peakScale, setPeakScale] = useState<number>(1.2);
  const [offpeakScale, setOffpeakScale] = useState<number>(1.0);
  const [flattenRatio, setFlattenRatio] = useState<number>(0);
  const [scenarioId, setScenarioId] = useState<string>("energy_baseline");
  const [predictedEnergy, setPredictedEnergy] = useState<ChartPoint[]>([]);
  const [predicting, setPredicting] = useState(false);
  const [predictError, setPredictError] = useState<string | null>(null);
  const [optimalEnergy, setOptimalEnergy] = useState<ChartPoint[]>([]);
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);
  const chartRef = useRef<ChartExportHandle | null>(null);
  const [exportTarget, setExportTarget] = useState<EnergyExportTarget | null>(
    null,
  );
  const zoneId = selectedArea ? selectedArea.name : null;
  const scenarioLabel = getEnergyScenarioLabel(scenarioId);
  const scenarioClass = getEnergyScenarioClass(scenarioId);
  const { points: energyPoints, loading: energyLoading } = useEnergySeries(
    selectedArea ? selectedArea.id : null,
  );
  const {
    points: simulateEnergyPoints,
    loading: simulateEnergyLoading,
    error: simulateEnergyError,
  } = useSimulationSeries(
    "energy",
    !!selectedArea && mode === "SIMULATE",
    {
      areaId: selectedArea?.id ?? null,
      parameters: {
        demand_scale: demandScale,
        peak_hour_shift: peakShift,
        peak_scale: peakScale,
        offpeak_scale: offpeakScale,
        flatten_ratio: flattenRatio,
      },
      runKey: simulateRun,
    },
  );

  const basePoints = energyPoints;

  const advisorySnapshot = useMemo(() => {
    const series: { metric: "energy"; label: string; points: ChartPoint[] }[] = [];

    if (basePoints.length) {
      series.push({ metric: "energy", label: "Real", points: basePoints });
    }
    if (
      mode === "REAL" &&
      predictedEnergy.length === basePoints.length &&
      predictedEnergy.length
    ) {
      series.push({ metric: "energy", label: "Predicted", points: predictedEnergy });
    }
    if (
      mode === "SIMULATE" &&
      simulateRun > 0 &&
      simulateEnergyPoints.length === basePoints.length
    ) {
      series.push({
        metric: "energy",
        label: "Simulated",
        points: simulateEnergyPoints,
      });
    }
    if (optimize && optimalEnergy.length === basePoints.length && optimalEnergy.length) {
      series.push({ metric: "energy", label: "Optimal", points: optimalEnergy });
    }

    return {
      active_view: mode,
      series,
    };
  }, [
    basePoints,
    mode,
    predictedEnergy,
    simulateRun,
    simulateEnergyPoints,
    optimize,
    optimalEnergy,
  ]);

  const { insights, loading, error } = useAdvisory(
    "energy",
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

  const runEnergyForecast = async () => {
    setMode("REAL");
    setOptimize(false);
    setSimulateRun(0);
    setPredictError(null);

    if (!basePoints.length) {
      setPredictedEnergy([]);
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
        target: "energy",
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
        setPredictedEnergy(mapped);
      } else {
        setPredictedEnergy(computeEnergyTrend(basePoints));
      }
    } catch (err) {
      setPredictError(
        err instanceof Error ? err.message : "Failed to compute forecast.",
      );
      setPredictedEnergy(computeEnergyTrend(basePoints));
    } finally {
      setPredicting(false);
    }
  };

  const handlePredictClick = () => {
    void runEnergyForecast();
  };

  useEffect(() => {
    if (mode === "SIMULATE" && optimize && basePoints.length && simulateEnergyPoints.length) {
      setOptimalEnergy(computeEnergyOptimal(basePoints, simulateEnergyPoints));
    }
    if (!optimize) {
      setOptimalEnergy([]);
    }
  }, [mode, optimize, basePoints, simulateEnergyPoints]);

  const energySeries: ChartSeries[] = [];
  if (basePoints.length) {
    energySeries.push({ label: "Real", color: "#f87b14", points: basePoints });
  }
  if (mode === "REAL" && predictedEnergy.length === basePoints.length && predictedEnergy.length) {
    energySeries.push({ label: "Predicted", color: "#de3388", points: predictedEnergy });
  }
  if (mode === "SIMULATE" && simulateRun > 0 && simulateEnergyPoints.length === basePoints.length) {
    energySeries.push({ label: "Simulated", color: "#1b55ce", points: simulateEnergyPoints });
  }
  if (optimize && optimalEnergy.length === basePoints.length && optimalEnergy.length) {
    energySeries.push({ label: "Optimal", color: "#08c44d", points: optimalEnergy });
  }

  const handleOpenFullExport = () => {
    setExportTarget({ kind: "page" });
    setIsExportDialogOpen(true);
  };

  const handleOpenTableExport = () => {
    setExportTarget({ kind: "table", id: "demand" });
    setIsExportDialogOpen(true);
  };

  const handleOpenChartExport = () => {
    setExportTarget({ kind: "chart", id: "consumption" });
    setIsExportDialogOpen(true);
  };

  const buildExportPage = (
    target: EnergyExportTarget,
    chartImage?: string | null,
  ): ExportPage => {
    const areaName = selectedArea?.name ?? "No area selected";
    const description = selectedArea
      ? `Energy module for ${selectedArea.name} in ${mode} mode.`
      : "Energy module showing baseline hourly demand profile.";
    const insightsText =
      selectedArea && !loading && !error && insights ? insights : undefined;

    const tables =
      target.kind === "chart"
        ? []
        : [
            {
              title: "Hourly energy demand",
              columns: ["Hour", "Demand (MWh)"],
              rows:
                basePoints && basePoints.length
                  ? basePoints.map((p) => [
                      String(p.x),
                      p.y.toFixed(2),
                    ])
                  : [["—", "—"]],
            },
          ];

    const charts =
      target.kind === "table"
        ? []
        : [
            {
              title: "Energy Consumption",
              x_label: "Hour of day",
              y_label: "Demand (MWh)",
              series: energySeries.map((s) => ({
                label: s.label,
                points: s.points,
              })),
              image_data: chartImage ?? undefined,
            },
          ];

    return {
      page_name: "Energy",
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
    let chartImage: string | null = null;
    try {
      chartImage = chartRef.current ? await chartRef.current.capturePng() : null;
    } catch (err) {
      console.error("Failed to capture chart image", err);
      // Proceed with export without the image
    }
    const page = buildExportPage(exportTarget, chartImage);    const payload: ExportPayload = {
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
          ? `SUSPS - Energy${areaNameFragment}`
          : exportTarget.kind === "table"
          ? `SUSPS - Energy - Demand table${areaNameFragment}`
          : `SUSPS - Energy - Consumption chart${areaNameFragment}`;
      const ext = format === "pdf" ? ".pdf" : format === "csv" ? ".csv" : ".zip";
      downloadBlob(blob, `${baseName}${ext}`);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("Failed to export Energy data", err);
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
                setScenarioId("energy_baseline");
              } else {
                setScenarioId((prev) =>
                  prev === "energy_baseline" ? "energy_simulate" : prev,
                );
              }
            }}
          />
        </div>
      </div>

      <DescriptionSection title="Energy Demand Overview">
        {selectedArea ? (
          <>
            In REAL mode, the table and line chart show the baseline hourly
            electricity demand profile for {selectedArea.name}: each row and point
            is one hour of a representative day, with demand expressed in MWh.
            This profile comes directly from the SUSPS pipeline for the selected
            area.
            <br />
            In SIMULATE mode, the same hourly structure is preserved but the values
            are adjusted using your scenario settings: demand scaling, peak-hour
            shifting, different multipliers for peak vs off-peak hours, and an
            optional flattening toward the daily average. This lets you explore how
            interventions like demand response or tariff changes could reshape the
            load curve relative to the baseline.
          </>
        ) : (
          <>
            Select an area from the sidebar to view its baseline hourly energy
            demand profile in REAL mode. After selecting an area, switch to
            SIMULATE to apply scaling, peak shifting, and flattening parameters and
            see how the demand curve could change under different scenarios.
          </>
        )}
      </DescriptionSection>

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
                setScenarioId("energy_baseline");
                setDemandScale(1.0);
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
                setScenarioId("energy_peak_spike");
                setDemandScale(1.2);
                setPeakShift(0);
                setPeakScale(1.3);
                setOffpeakScale(1.0);
                setFlattenRatio(0);
              }}
              className="rounded-full bg-amber-50 px-3 py-1 text-amber-700 hover:bg-amber-100"
            >
              Evening peak spike
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("SIMULATE");
                setScenarioId("energy_demand_response");
                setDemandScale(1.0);
                setPeakShift(0);
                setPeakScale(0.75);
                setOffpeakScale(1.1);
                setFlattenRatio(0.4);
              }}
              className="rounded-full bg-emerald-50 px-3 py-1 text-emerald-700 hover:bg-emerald-100"
            >
              Demand response pilot
            </button>
          </div>
          <p className="mb-3 text-xs text-gray-600">
            Adjust the demand scale, peak-hour timing, and flattening, then
            switch to Simulate mode to see how the daily profile changes.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Demand scale
              </label>
              <input
                type="number"
                min={0.5}
                max={2}
                step={0.1}
                value={demandScale}
                onChange={(e) =>
                  setDemandScale(Number(e.target.value) || 0)
                }
                className="w-full rounded-md border border-neutral-300 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-neutral-400"
              />
              <p className="mt-1 text-[11px] text-gray-500">
                1.0 = baseline; values &gt;1 increase demand, values &lt;1 decrease it.
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
                earlier (e.g. demand response or staggered working hours).
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
                Use to model measures like time-of-use tariffs or targeted load
                shifting.
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
                0 = keep current shape; values closer to 1 flatten peaks and fill
                valleys (e.g. strong demand response programs).
              </p>
            </div>
          </div>
        </section>
      )}

      <Table
        title="Energy demand table"
        onExport={handleOpenTableExport}
        columns={["Hour", "Demand (MWh)"]}
        rows={
          selectedArea && basePoints.length > 0
            ? basePoints.map((p, idx) => {
                const real = Number(p.y.toFixed(2));
                const pred =
                  mode === "REAL" && predictedEnergy[idx]
                    ? Number(predictedEnergy[idx].y.toFixed(2))
                    : null;
                const sim =
                  mode === "SIMULATE" && simulateRun > 0 && simulateEnergyPoints[idx]
                    ? Number(simulateEnergyPoints[idx].y.toFixed(2))
                    : null;
                const opt =
                  optimize && optimalEnergy[idx]
                    ? Number(optimalEnergy[idx].y.toFixed(2))
                    : null;
                return [
                  p.x,
                  (
                    <>
                      {real.toFixed(2)}
                      {pred !== null && (
                        <span className="ml-1 text-[11px] text-[#de3388]">
                          ({pred.toFixed(2)})
                        </span>
                      )}
                      {sim !== null && (
                        <span className="ml-1 text-[11px] text-[#1b55ce]">
                          ({sim.toFixed(2)})
                        </span>
                      )}
                      {opt !== null && (
                        <span className="ml-1 text-[11px] text-[#08c44d]">
                          ({opt.toFixed(2)})
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
        <LineChart
          ref={chartRef}
          title="Energy Consumption"
          series={energySeries}
          xLabel="Hour of day"
          yLabel="Demand (MWh)"
          onExport={handleOpenChartExport}
        />
        <HotspotMap optimize={optimize} zoneId={selectedArea?.name ?? null} />
      </div>

      {selectedArea && energyLoading && (
        <p className="text-xs text-gray-500">Loading energy series...</p>
      )}
      {selectedArea && predicting && !energyLoading && (
        <p className="text-xs text-gray-500">Computing forecast overlay...</p>
      )}
      {selectedArea && predictError && (
        <p className="text-xs text-red-600">{predictError}</p>
      )}
      {selectedArea && mode === "SIMULATE" && simulateEnergyLoading && (
        <p className="text-xs text-gray-500">Loading simulated energy...</p>
      )}
      {selectedArea && mode === "SIMULATE" && simulateEnergyError && (
        <p className="text-xs text-red-600">{simulateEnergyError}</p>
      )}

      <InsightsSection>
        {!selectedArea && (
          <p>Select an area to generate detailed energy advisory.</p>
        )}
        {selectedArea && loading && <p>Loading advisory...</p>}
        {selectedArea && error && (
          <p className="text-red-600 text-sm">{error}</p>
        )}
        {selectedArea && !loading && !error && insights && (
          <>
            <FormattedInsights text={insights} />
            {scenarioId !== "energy_baseline" && (
              <p className="mt-2 text-[11px] text-gray-500">
                Scenario: {scenarioLabel}
              </p>
            )}
          </>
        )}
        {selectedArea && optimize && (
          <p className="mt-2 text-xs text-emerald-700">
            With Optimize active, pay attention to the green optimal zones on the
            hotspot map  these are areas where forecast energy risk improves
            relative to current hotspot levels.
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

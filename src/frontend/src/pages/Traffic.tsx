import { useEffect, useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { ModeToggle } from "../components/ModeToggle";
import { DescriptionSection } from "../components/DescriptionSection";
import { Table } from "../components/Table";
import { Histogram } from "../components/Histogram";
import { HotspotMap } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { ActionToggle } from "../components/ActionToggle";
import { FormattedInsights } from "../components/FormattedInsights";
import type { Area, Mode, ChartPoint, ChartSeries } from "../types";
import { useAdvisory } from "../hooks/useAdvisory";
import { useTrafficSeries } from "../hooks/useSeries";
import { useSimulationSeries } from "../hooks/useSimulation";

interface TrafficPageProps {
  selectedArea: Area | null;
}

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

export function TrafficPage({ selectedArea }: TrafficPageProps) {
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
  const [optimalTraffic, setOptimalTraffic] = useState<ChartPoint[]>([]);
  const zoneId = selectedArea ? selectedArea.name : null;
  const scenarioLabel = getTrafficScenarioLabel(scenarioId);
  const scenarioClass = getTrafficScenarioClass(scenarioId);
  const { insights, loading, error } = useAdvisory("traffic", zoneId, scenarioId);
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
          title="Traffic Volume"
          series={trafficSeries}
          xLabel="Hour of day"
          yLabel="Volume (veh/hr)"
        />
        <HotspotMap optimize={optimize} zoneId={selectedArea?.name ?? null} />
      </div>

      {selectedArea && trafficLoading && (
        <p className="text-xs text-gray-500">Loading traffic series...</p>
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

      <ActionToggle
        mode={mode}
        onPredict={() => {
          setMode("REAL");
          setOptimize(false);
          setSimulateRun(0);
          if (trafficPoints.length) {
            setPredictedTraffic(computeTrafficTrend(trafficPoints));
          } else {
            setPredictedTraffic([]);
          }
        }}
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

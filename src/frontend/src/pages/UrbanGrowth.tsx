import { useEffect, useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { ModeToggle } from "../components/ModeToggle";
import { DescriptionSection } from "../components/DescriptionSection";
import { Table } from "../components/Table";
import { BarChart } from "../components/BarChart";
import { HotspotMap } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { FormattedInsights } from "../components/FormattedInsights";
import { ActionToggle } from "../components/ActionToggle";
import type { Area, Mode, ChartPoint, ChartSeries } from "../types";
import { useAdvisory } from "../hooks/useAdvisory";
import { useGrowthSeries } from "../hooks/useSeries";
import { useSimulationSeries } from "../hooks/useSimulation";

interface UrbanGrowthPageProps {
  selectedArea: Area | null;
}

function getGrowthScenarioLabel(id: string): string {
  switch (id) {
    case "growth_baseline":
      return "Baseline";
    case "growth_new_housing":
      return "New housing estate";
    case "growth_slowdown":
      return "Slowdown";
    case "growth_relocation_shock":
      return "Relocation shock";
    case "growth_simulate":
      return "Custom simulate";
    default:
      return "Custom simulate";
  }
}

function getGrowthScenarioClass(id: string): string {
  switch (id) {
    case "growth_baseline":
      return "bg-slate-100 text-slate-700";
    case "growth_new_housing":
      return "bg-emerald-50 text-emerald-700";
    case "growth_slowdown":
      return "bg-amber-100 text-amber-800";
    case "growth_relocation_shock":
      return "bg-red-50 text-red-700";
    case "growth_simulate":
      return "bg-slate-100 text-slate-700";
    default:
      return "bg-slate-100 text-slate-700";
  }
}

function computeTrendSeries(points: ChartPoint[]): ChartPoint[] {
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

function computeOptimalSeries(real: ChartPoint[], sim: ChartPoint[]): ChartPoint[] {
  const len = Math.min(real.length, sim.length);
  const out: ChartPoint[] = [];
  for (let i = 0; i < len; i += 1) {
    const r = real[i];
    const s = sim[i];
    out.push({ x: r.x, y: (r.y + s.y) / 2 });
  }
  return out;
}

export function UrbanGrowthPage({ selectedArea }: UrbanGrowthPageProps) {
  const [mode, setMode] = useState<Mode>("REAL");
  const [optimize, setOptimize] = useState(false);
  const [simulateRun, setSimulateRun] = useState(0);
  const [populationScale, setPopulationScale] = useState<number>(1.1);
  const [annualRateDelta, setAnnualRateDelta] = useState<number>(0);
  const [shockYear, setShockYear] = useState<number | null>(null);
  const [shockPct, setShockPct] = useState<number>(0);
  const [scenarioId, setScenarioId] = useState<string>("growth_baseline");
  const [predictedGrowth, setPredictedGrowth] = useState<ChartPoint[]>([]);
  const [optimalGrowth, setOptimalGrowth] = useState<ChartPoint[]>([]);
  const zoneId = selectedArea ? selectedArea.name : null;
  const scenarioLabel = getGrowthScenarioLabel(scenarioId);
  const scenarioClass = getGrowthScenarioClass(scenarioId);
  const { insights, loading, error } = useAdvisory("growth", zoneId, scenarioId);
  const { points: growthPoints, loading: growthLoading } = useGrowthSeries(
    selectedArea ? selectedArea.id : null,
  );
  const {
    points: simulateGrowthPoints,
    loading: simulateGrowthLoading,
    error: simulateGrowthError,
  } = useSimulationSeries(
    "growth",
    !!selectedArea && mode === "SIMULATE",
    {
      areaId: selectedArea?.id ?? null,
      parameters: {
        population_scale: populationScale,
        annual_rate_delta_pct: annualRateDelta,
        shock_year: shockYear ?? undefined,
        shock_pct: shockPct,
      },
      runKey: simulateRun,
    },
  );
  const basePoints = growthPoints;

  useEffect(() => {
    if (mode === "SIMULATE" && optimize && basePoints.length && simulateGrowthPoints.length) {
      setOptimalGrowth(computeOptimalSeries(basePoints, simulateGrowthPoints));
    }
    if (!optimize) {
      setOptimalGrowth([]);
    }
  }, [mode, optimize, basePoints, simulateGrowthPoints]);

  const growthSeries: ChartSeries[] = [];
  if (basePoints.length) {
    growthSeries.push({ label: "Real", color: "#91e03f", points: basePoints });
  }
  if (mode === "REAL" && predictedGrowth.length === basePoints.length && predictedGrowth.length) {
    growthSeries.push({ label: "Predicted", color: "#de3388", points: predictedGrowth });
  }
  if (mode === "SIMULATE" && simulateRun > 0 && simulateGrowthPoints.length === basePoints.length) {
    growthSeries.push({ label: "Simulated", color: "#1b55ce", points: simulateGrowthPoints });
  }
  if (optimize && optimalGrowth.length === basePoints.length && optimalGrowth.length) {
    growthSeries.push({ label: "Optimal", color: "#08c44d", points: optimalGrowth });
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
                setScenarioId("growth_baseline");
              } else {
                // Generic simulate label unless a preset overrides it
                setScenarioId((prev) =>
                  prev === "growth_baseline" ? "growth_simulate" : prev,
                );
              }
            }}
          />
        </div>
      </div>

      <DescriptionSection title="Urban Growth Overview">
        {selectedArea ? (
          <>
            In REAL mode, the table and chart below show the baseline population
            history and forecasts for {selectedArea.name} that SUSPS has
            generated from the underlying growth model. Each row in the table is a
            year, and each bar in the chart is the corresponding predicted
            population for that year.
            <br />
            In SIMULATE mode, the same structure is preserved but the values are
            re-computed using your scenario parameters: a global population scale,
            an adjustment to the annual growth rate, and an optional one-off shock
            in a specific year. This lets you compare the baseline growth
            trajectory with alternative futures for densification, slowdown, or
            relocation shocks while the hotspot map highlights spatial risk.
          </>
        ) : (
          <>
            Select an area from the sidebar to view its baseline population
            history and forecasts in REAL mode. Once an area is selected, you can
            switch to SIMULATE to apply growth-rate and shock assumptions and see
            how the yearly population trajectory would change.
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
                setScenarioId("growth_baseline");
                setPopulationScale(1.0);
                setAnnualRateDelta(0);
                setShockYear(null);
                setShockPct(0);
              }}
              className="rounded-full bg-neutral-200 px-3 py-1 text-gray-800 hover:bg-neutral-300"
            >
              Baseline
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("SIMULATE");
                setScenarioId("growth_new_housing");
                setPopulationScale(1.15);
                setAnnualRateDelta(1.5);
                setShockYear(null);
                setShockPct(0);
              }}
              className="rounded-full bg-emerald-50 px-3 py-1 text-emerald-700 hover:bg-emerald-100"
            >
              New housing estate
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("SIMULATE");
                setScenarioId("growth_slowdown");
                setPopulationScale(1.0);
                setAnnualRateDelta(-1.0);
                setShockYear(null);
                setShockPct(0);
              }}
              className="rounded-full bg-amber-100 px-3 py-1 text-amber-800 hover:bg-amber-200"
            >
              Slowdown
            </button>
            <button
              type="button"
              onClick={() => {
                setMode("SIMULATE");
                setScenarioId("growth_relocation_shock");
                setPopulationScale(1.0);
                setAnnualRateDelta(0);
                setShockYear(new Date().getFullYear() + 3);
                setShockPct(-10);
              }}
              className="rounded-full bg-red-50 px-3 py-1 text-red-700 hover:bg-red-100"
            >
              Relocation shock
            </button>
          </div>
          <p className="mb-3 text-xs text-gray-600">
            Adjust the population scale, annual growth-rate delta, and optional
            one-off shocks, then switch to Simulate mode to see how the
            long-term trajectory changes.
          </p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Population scale
              </label>
              <input
                type="number"
                min={0.5}
                max={2}
                step={0.1}
                value={populationScale}
                onChange={(e) =>
                  setPopulationScale(Number(e.target.value) || 0)
                }
                className="w-full rounded-md border border-neutral-300 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-neutral-400"
              />
              <p className="mt-1 text-[11px] text-gray-500">
                1.0 = baseline; values &gt;1 increase all populations, values &lt;1
                decrease them.
              </p>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Annual rate delta (% points)
              </label>
              <input
                type="number"
                min={-5}
                max={5}
                step={0.5}
                value={annualRateDelta}
                onChange={(e) =>
                  setAnnualRateDelta(Number(e.target.value) || 0)
                }
                className="w-full rounded-md border border-neutral-300 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-neutral-400"
              />
              <p className="mt-1 text-[11px] text-gray-500">
                Positive values speed up growth; negative values slow it down.
                Useful for scenarios like "new housing estate" or stricter land
                use controls.
              </p>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                One-off shock year (optional)
              </label>
              <input
                type="number"
                min={1900}
                max={2100}
                step={1}
                value={shockYear ?? ""}
                onChange={(e) => {
                  const v = Number(e.target.value);
                  if (Number.isNaN(v)) {
                    setShockYear(null);
                  } else {
                    setShockYear(v);
                  }
                }}
                className="w-full rounded-md border border-neutral-300 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-neutral-400"
              />
              <p className="mt-1 text-[11px] text-gray-500">
                Year in which a discrete population shock occurs (e.g. large
                inward migration or relocation).
              </p>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-700">
                Shock size (% of that year population)
              </label>
              <input
                type="number"
                min={-50}
                max={50}
                step={1}
                value={shockPct}
                onChange={(e) => setShockPct(Number(e.target.value) || 0)}
                className="w-full rounded-md border border-neutral-300 px-2 py-1 text-xs focus:outline-none focus:ring-2 focus:ring-neutral-400"
              />
              <p className="mt-1 text-[11px] text-gray-500">
                Positive values add population in the shock year; negative values
                represent sudden losses (e.g. relocation or hazard).
              </p>
            </div>
          </div>
        </section>
      )}

      <Table
        columns={["Year", "Population"]}
        rows={
          selectedArea && basePoints.length > 0
            ? basePoints.map((p, idx) => {
                const real = Math.round(p.y);
                const pred =
                  mode === "REAL" && predictedGrowth[idx]
                    ? Math.round(predictedGrowth[idx].y)
                    : null;
                const sim =
                  mode === "SIMULATE" && simulateRun > 0 && simulateGrowthPoints[idx]
                    ? Math.round(simulateGrowthPoints[idx].y)
                    : null;
                const opt =
                  optimize && optimalGrowth[idx]
                    ? Math.round(optimalGrowth[idx].y)
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
        <BarChart
          title="Population Growth"
          series={growthSeries}
          xLabel="Year"
          yLabel="Population"
        />
        <HotspotMap optimize={optimize} zoneId={selectedArea?.name ?? null} />
      </div>

      {selectedArea && growthLoading && (
        <p className="text-xs text-gray-500">Loading growth series...</p>
      )}
      {selectedArea && mode === "SIMULATE" && simulateGrowthLoading && (
        <p className="text-xs text-gray-500">Loading simulated growth...</p>
      )}
      {selectedArea && mode === "SIMULATE" && simulateGrowthError && (
        <p className="text-xs text-red-600">{simulateGrowthError}</p>
      )}

      <InsightsSection>
        {!selectedArea && (
          <p>
            Select an area to generate detailed growth advisory for that city or
            zone.
          </p>
        )}
        {selectedArea && loading && <p>Loading advisory...</p>}
        {selectedArea && error && (
          <p className="text-red-600 text-sm">{error}</p>
        )}
        {selectedArea && !loading && !error && insights && (
          <>
            <FormattedInsights text={insights} />
            {scenarioId !== "growth_baseline" && (
              <p className="mt-2 text-[11px] text-gray-500">
                Scenario: {scenarioLabel}
              </p>
            )}
          </>
        )}
        {selectedArea && optimize && (
          <p className="mt-2 text-xs text-emerald-700">
            With Optimize active, focus on the green optimal zones on the hotspot
            map  these are hotspots where the forecast risk improves compared
            to today.
          </p>
        )}
      </InsightsSection>

      <ActionToggle
        mode={mode}
        onPredict={() => {
          setMode("REAL");
          setOptimize(false);
          setSimulateRun(0);
          if (growthPoints.length) {
            setPredictedGrowth(computeTrendSeries(growthPoints));
          } else {
            setPredictedGrowth([]);
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

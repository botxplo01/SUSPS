import { useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { ModeToggle } from "../components/ModeToggle";
import { DescriptionSection } from "../components/DescriptionSection";
import { Table } from "../components/Table";
import { LineChart } from "../components/LineChart";
import { Map } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { ActionToggle } from "../components/ActionToggle";
import type { Area, Mode } from "../types";
import { useAdvisory } from "../hooks/useAdvisory";
import { useEnergySeries } from "../hooks/useSeries";
import { useSimulationSeries } from "../hooks/useSimulation";

interface EnergyPageProps {
  selectedArea: Area | null;
}

export function EnergyPage({ selectedArea }: EnergyPageProps) {
  const [mode, setMode] = useState<Mode>("REAL");
  const [optimize, setOptimize] = useState(false);
  const [demandScale, setDemandScale] = useState<number>(1.1);
  const [peakShift, setPeakShift] = useState<number>(0);
  const zoneId = selectedArea ? selectedArea.name : null;
  const { insights, loading, error } = useAdvisory("energy", zoneId);
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
      },
    },
  );
  const chartPoints = mode === "SIMULATE" ? simulateEnergyPoints : energyPoints;

  return (
    <div className="space-y-4 pb-16">
      <div className="flex items-center justify-between">
        <AreaBadge name={selectedArea?.name ?? "No area selected"} />
        <ModeToggle
          mode={mode}
          onChange={(next) => {
            setMode(next);
            setOptimize(false);
          }}
        />
      </div>

      <DescriptionSection title="Energy Description">
        {selectedArea ? (
          <>
            Inspect current and forecasted energy demand for {selectedArea.name}.
            Use Real mode to view baseline demand and Simulate mode to explore
            hypothetical demand spikes and mitigation strategies.
          </>
        ) : (
          <>
            Select an area from the sidebar to load energy usage and forecast
            summaries.
          </>
        )}
      </DescriptionSection>

      {selectedArea && (
        <section className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold text-gray-800">
            Simulation parameters
          </h2>
          <p className="mb-3 text-xs text-gray-600">
            Adjust the demand scale and peak-hour shift, then switch to Simulate
            mode to see how the daily profile changes.
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
                earlier.
              </p>
            </div>
          </div>
        </section>
      )}

      <Table
        columns={["Hour", "Demand (MWh)"]}
        rows={
          selectedArea && chartPoints.length > 0
            ? chartPoints.map((p) => [p.x, Number(p.y.toFixed(2))])
            : [["—", "—"]]
        }
      />

      <div className="grid gap-4 md:grid-cols-2">
        <LineChart title="Energy Consumption" data={chartPoints} />
        <Map optimize={optimize} zoneId={selectedArea?.name ?? null} />
      </div>

      {selectedArea && energyLoading && (
        <p className="text-xs text-gray-500">Loading energy series...</p>
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
          <pre className="whitespace-pre-wrap text-sm text-gray-800">
            {insights}
          </pre>
        )}
        {selectedArea && optimize && (
          <p className="mt-2 text-xs text-emerald-700">
            With Optimize active, pay attention to the green optimal zones on the
            hotspot map  these are areas where forecast energy risk improves
            relative to current hotspot levels.
          </p>
        )}
      </InsightsSection>

      <ActionToggle
        mode={mode}
        onPredict={() => {
          setMode("REAL");
          setOptimize(false);
        }}
        onOptimize={() => {
          setOptimize(true);
        }}
        onSimulate={() => {
          setMode("SIMULATE");
          setOptimize(false);
        }}
      />
    </div>
  );
}

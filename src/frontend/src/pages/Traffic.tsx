import { useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { ModeToggle } from "../components/ModeToggle";
import { DescriptionSection } from "../components/DescriptionSection";
import { Table } from "../components/Table";
import { Histogram } from "../components/Histogram";
import { HotspotMap } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { ActionToggle } from "../components/ActionToggle";
import { FormattedInsights } from "../components/FormattedInsights";
import type { Area, Mode } from "../types";
import { useAdvisory } from "../hooks/useAdvisory";
import { useTrafficSeries } from "../hooks/useSeries";
import { useSimulationSeries } from "../hooks/useSimulation";

interface TrafficPageProps {
  selectedArea: Area | null;
}

export function TrafficPage({ selectedArea }: TrafficPageProps) {
  const [mode, setMode] = useState<Mode>("REAL");
  const [optimize, setOptimize] = useState(false);
  const [volumeScale, setVolumeScale] = useState<number>(1.1);
  const [peakShift, setPeakShift] = useState<number>(0);
  const zoneId = selectedArea ? selectedArea.name : null;
  const { insights, loading, error } = useAdvisory("traffic", zoneId);
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
      },
    },
  );
  const chartPoints =
    mode === "SIMULATE" ? simulateTrafficPoints : trafficPoints;

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

      <DescriptionSection title="Traffic Description">
        {selectedArea ? (
          <>
            Explore current traffic flow, congestion hotspots, and predicted
            patterns in {selectedArea.name}. Use Simulate to explore routing or
            demand scenarios.
          </>
        ) : (
          <>
            Select an area from the sidebar to view traffic summaries and
            congestion hotspots.
          </>
        )}
      </DescriptionSection>

      {selectedArea && (
        <section className="rounded-xl bg-white p-4 shadow-sm">
          <h2 className="mb-2 text-sm font-semibold text-gray-800">
            Simulation parameters
          </h2>
          <p className="mb-3 text-xs text-gray-600">
            Adjust the traffic volume scale and peak-hour shift, then switch to
            Simulate mode to see how the hourly profile changes.
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
                earlier.
              </p>
            </div>
          </div>
        </section>
      )}

      <Table
        columns={["Hour", "Volume (veh/hr)"]}
        rows={
          selectedArea && chartPoints.length > 0
            ? chartPoints.map((p) => [p.x, Math.round(p.y)])
            : [["—", "—"]]
        }
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Histogram
          title="Traffic Volume"
          data={chartPoints}
          accentColor="#f24152"
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
          <FormattedInsights text={insights} />
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

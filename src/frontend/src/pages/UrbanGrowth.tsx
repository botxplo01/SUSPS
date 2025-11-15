import { useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { ModeToggle } from "../components/ModeToggle";
import { DescriptionSection } from "../components/DescriptionSection";
import { Table } from "../components/Table";
import { BarChart } from "../components/BarChart";
import { HotspotMap } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { ActionToggle } from "../components/ActionToggle";
import type { Area, Mode } from "../types";
import { useAdvisory } from "../hooks/useAdvisory";
import { useGrowthSeries } from "../hooks/useSeries";
import { useSimulationSeries } from "../hooks/useSimulation";

interface UrbanGrowthPageProps {
  selectedArea: Area | null;
}

export function UrbanGrowthPage({ selectedArea }: UrbanGrowthPageProps) {
  const [mode, setMode] = useState<Mode>("REAL");
  const [optimize, setOptimize] = useState(false);
  const zoneId = selectedArea ? selectedArea.name : null;
  const { insights, loading, error } = useAdvisory("growth", zoneId);
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
      parameters: { population_scale: 1.1 },
    },
  );
  const chartPoints = mode === "SIMULATE" ? simulateGrowthPoints : growthPoints;

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

      <DescriptionSection title="Urban Growth Description">
        {selectedArea ? (
          <>
            View population growth statistics, census tables, and forecasted
            density for {selectedArea.name}. Use Real mode to inspect the current
            state and Simulate mode to explore hypothetical scenarios.
          </>
        ) : (
          <>
            Select an area from the sidebar to explore urban growth statistics.
            Until an area is selected, only this description and placeholders are
            shown.
          </>
        )}
      </DescriptionSection>

      <Table
        columns={["Year", "Population"]}
        rows={
          selectedArea && chartPoints.length > 0
            ? chartPoints.map((p) => [p.x, Math.round(p.y)])
            : [["—", "—"]]
        }
      />

      <div className="grid gap-4 md:grid-cols-2">
        <BarChart title="Population Growth" data={chartPoints} />
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
          <pre className="whitespace-pre-wrap text-sm text-gray-800">
            {insights}
          </pre>
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

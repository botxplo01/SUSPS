import { useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { ModeToggle } from "../components/ModeToggle";
import { DescriptionSection } from "../components/DescriptionSection";
import { Table } from "../components/Table";
import { BarChart } from "../components/BarChart";
import { Map } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { ActionToggle } from "../components/ActionToggle";
import type { Area, Mode } from "../types";
import { useAdvisory } from "../hooks/useAdvisory";
import { useGrowthSeries } from "../hooks/useSeries";

interface UrbanGrowthPageProps {
  selectedArea: Area | null;
}

export function UrbanGrowthPage({ selectedArea }: UrbanGrowthPageProps) {
  const [mode, setMode] = useState<Mode>("REAL");
  const zoneId = selectedArea ? selectedArea.name : null;
  const { insights, loading, error } = useAdvisory("growth", zoneId);
  const { points: growthPoints, loading: growthLoading } = useGrowthSeries(
    selectedArea ? selectedArea.id : null,
  );

  return (
    <div className="space-y-4 pb-16">
      <div className="flex items-center justify-between">
        <AreaBadge name={selectedArea?.name ?? "No area selected"} />
        <ModeToggle mode={mode} onChange={setMode} />
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
        rows={[["2020", 0], ["2025", 0]]}
      />

      <div className="grid gap-4 md:grid-cols-2">
        <BarChart title="Population Growth" data={growthPoints} />
        <Map />
      </div>

      {selectedArea && growthLoading && (
        <p className="text-xs text-gray-500">Loading growth series...</p>
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
      </InsightsSection>

      <ActionToggle
        onPredict={() => setMode("REAL")}
        onSimulate={() => setMode("SIMULATE")}
      />
    </div>
  );
}

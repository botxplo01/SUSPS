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

interface EnergyPageProps {
  selectedArea: Area | null;
}

export function EnergyPage({ selectedArea }: EnergyPageProps) {
  const [mode, setMode] = useState<Mode>("REAL");
  const zoneId = selectedArea ? selectedArea.name : null;
  const { insights, loading, error } = useAdvisory("energy", zoneId);
  const { points: energyPoints, loading: energyLoading } = useEnergySeries(
    selectedArea ? selectedArea.id : null,
  );

  return (
    <div className="space-y-4 pb-16">
      <div className="flex items-center justify-between">
        <AreaBadge name={selectedArea?.name ?? "No area selected"} />
        <ModeToggle mode={mode} onChange={setMode} />
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

      <Table
        columns={["Sector", "Usage"]}
        rows={[["Residential", 0], ["Industrial", 0]]}
      />

      <div className="grid gap-4 md:grid-cols-2">
        <LineChart title="Energy Consumption" data={energyPoints} />
        <Map />
      </div>

      {selectedArea && energyLoading && (
        <p className="text-xs text-gray-500">Loading energy series...</p>
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
      </InsightsSection>

      <ActionToggle
        onPredict={() => setMode("REAL")}
        onSimulate={() => setMode("SIMULATE")}
      />
    </div>
  );
}

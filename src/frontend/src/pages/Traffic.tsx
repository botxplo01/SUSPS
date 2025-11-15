import { useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { ModeToggle } from "../components/ModeToggle";
import { DescriptionSection } from "../components/DescriptionSection";
import { Table } from "../components/Table";
import { Histogram } from "../components/Histogram";
import { Map } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { ActionToggle } from "../components/ActionToggle";
import type { Area, Mode } from "../types";
import { useAdvisory } from "../hooks/useAdvisory";
import { useTrafficSeries } from "../hooks/useSeries";

interface TrafficPageProps {
  selectedArea: Area | null;
}

export function TrafficPage({ selectedArea }: TrafficPageProps) {
  const [mode, setMode] = useState<Mode>("REAL");
  const zoneId = selectedArea ? selectedArea.name : null;
  const { insights, loading, error } = useAdvisory("traffic", zoneId);
  const { points: trafficPoints, loading: trafficLoading } = useTrafficSeries(
    selectedArea ? selectedArea.id : null,
  );

  return (
    <div className="space-y-4 pb-16">
      <div className="flex items-center justify-between">
        <AreaBadge name={selectedArea?.name ?? "No area selected"} />
        <ModeToggle mode={mode} onChange={setMode} />
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

      <Table
        columns={["Segment", "Flow"]}
        rows={[["Segment A", 0], ["Segment B", 0]]}
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Histogram title="Traffic Volume" data={trafficPoints} />
        <Map />
      </div>

      {selectedArea && trafficLoading && (
        <p className="text-xs text-gray-500">Loading traffic series...</p>
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

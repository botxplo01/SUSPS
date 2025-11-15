import { AreaBadge } from "../components/AreaBadge";
import { DescriptionSection } from "../components/DescriptionSection";
import { LineChart } from "../components/LineChart";
import { BarChart } from "../components/BarChart";
import { Map } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import type { Area } from "../types";
import { useAdvisory } from "../hooks/useAdvisory";
import { useGrowthSeries, useEnergySeries, useTrafficSeries } from "../hooks/useSeries";

interface DashboardPageProps {
  selectedArea: Area | null;
}

export function DashboardPage({ selectedArea }: DashboardPageProps) {
  const zoneId = selectedArea ? selectedArea.name : null;
  const areaId = selectedArea ? selectedArea.id : null;
  const { insights, loading, error } = useAdvisory("dashboard", zoneId);
  const { points: growthPoints } = useGrowthSeries(areaId);
  const { points: energyPoints } = useEnergySeries(areaId);
  const { points: trafficPoints } = useTrafficSeries(areaId);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <AreaBadge name={selectedArea?.name ?? "No area selected"} />
      </div>

      <DescriptionSection title="System Overview">
        {selectedArea ? (
          <>
            This dashboard summarizes urban growth, energy, and traffic for the
            selected area. Use the navigation to explore each module in more
            detail.
          </>
        ) : (
          <>
            Select an area from the sidebar to load data-driven summaries.
          </>
        )}
      </DescriptionSection>

      <div className="grid gap-4 md:grid-cols-2">
        <BarChart title="Urban Growth Summary" data={growthPoints} />
        <BarChart title="Energy Summary" data={energyPoints} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <LineChart title="Traffic Summary" data={trafficPoints} />
        <Map zoneId={selectedArea?.name ?? null} />
      </div>

      <InsightsSection>
        {!selectedArea && (
          <p>
            Select an area from the sidebar to generate AI advisory for this
            dashboard.
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
    </div>
  );
}

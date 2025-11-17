import { AreaBadge } from "../components/AreaBadge";
import { DescriptionSection } from "../components/DescriptionSection";
import { LineChart } from "../components/LineChart";
import { BarChart } from "../components/BarChart";
import { Histogram } from "../components/Histogram";
import { HotspotMap } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { FormattedInsights } from "../components/FormattedInsights";
import type { Area } from "../types";
import { useAdvisory } from "../hooks/useAdvisory";
import { useGrowthSeries, useEnergySeries, useTrafficSeries } from "../hooks/useSeries";

interface DashboardPageProps {
  selectedArea: Area | null;
}

export function DashboardPage({ selectedArea }: DashboardPageProps) {
  const zoneId = selectedArea ? selectedArea.name : null;
  const areaId = selectedArea ? selectedArea.id : null;
  const { insights, loading, error } = useAdvisory("dashboard", zoneId, "baseline");
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
            This dashboard shows the baseline (REAL) data that the system has
            ingested for {selectedArea.name} across urban growth, hourly energy
            demand, and traffic volumes. The charts below summarize the same
            underlying time series that each domain page uses: population by year,
            energy demand by hour of day, and traffic volumes by hour of day.
            Scenario-based SIMULATE views and parameter controls live on the
            individual Urban Growth, Energy, and Traffic pages.
          </>
        ) : (
          <>
            Select an area from the sidebar to load baseline (REAL) summaries of
            population, energy demand, and traffic. You can then switch to the
            individual modules to explore SIMULATE scenarios in more detail.
          </>
        )}
      </DescriptionSection>

      <div className="grid gap-4 md:grid-cols-2">
        <BarChart
          title="Urban Growth Summary"
          data={growthPoints}
          accentColor="#91e03f"
          xLabel="Year"
          yLabel="Population"
        />
        <LineChart
          title="Energy Summary"
          data={energyPoints}
          accentColor="#f87b14"
          xLabel="Hour of day"
          yLabel="Demand (MWh)"
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Histogram
          title="Traffic Summary"
          data={trafficPoints}
          accentColor="#f24152"
          xLabel="Hour of day"
          yLabel="Volume (veh/hr)"
        />
        <HotspotMap zoneId={selectedArea?.name ?? null} />
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
          <FormattedInsights text={insights} />
        )}
      </InsightsSection>
    </div>
  );
}

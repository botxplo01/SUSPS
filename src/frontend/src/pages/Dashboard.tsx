import { AreaBadge } from "../components/AreaBadge";
import { DescriptionSection } from "../components/DescriptionSection";
import { LineChart } from "../components/LineChart";
import { BarChart } from "../components/BarChart";
import { Map } from "../components/Map";

export function DashboardPage() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <AreaBadge name="Nairobi" />
      </div>

      <DescriptionSection title="System Overview">
        Overview of how the system works will be implemented here.
      </DescriptionSection>

      <div className="grid gap-4 md:grid-cols-2">
        <BarChart title="Urban Growth Summary" />
        <BarChart title="Energy Summary" />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <LineChart title="Traffic Summary" />
        <Map />
      </div>
    </div>
  );
}

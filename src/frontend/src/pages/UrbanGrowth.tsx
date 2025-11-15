import { useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { ModeToggle } from "../components/ModeToggle";
import { DescriptionSection } from "../components/DescriptionSection";
import { Table } from "../components/Table";
import { BarChart } from "../components/BarChart";
import { Map } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { ActionToggle } from "../components/ActionToggle";

export function UrbanGrowthPage() {
  const [mode, setMode] = useState<"REAL" | "SIMULATE">("REAL");

  return (
    <div className="space-y-4 pb-16">
      <div className="flex items-center justify-between">
        <AreaBadge name="Nairobi" />
        <ModeToggle mode={mode} onChange={setMode} />
      </div>

      <DescriptionSection title="Urban Growth Description" />

      <Table
        columns={["Year", "Population"]}
        rows={[["2020", 0], ["2025", 0]]}
      />

      <div className="grid gap-4 md:grid-cols-2">
        <BarChart title="Population Growth" />
        <Map />
      </div>

      <InsightsSection />

      <ActionToggle />
    </div>
  );
}

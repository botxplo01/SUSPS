import { useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { ModeToggle } from "../components/ModeToggle";
import { DescriptionSection } from "../components/DescriptionSection";
import { Table } from "../components/Table";
import { LineChart } from "../components/LineChart";
import { Map } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { ActionToggle } from "../components/ActionToggle";

export function EnergyPage() {
  const [mode, setMode] = useState<"REAL" | "SIMULATE">("REAL");

  return (
    <div className="space-y-4 pb-16">
      <div className="flex items-center justify-between">
        <AreaBadge name="Nairobi" />
        <ModeToggle mode={mode} onChange={setMode} />
      </div>

      <DescriptionSection title="Energy Description" />

      <Table
        columns={["Sector", "Usage"]}
        rows={[["Residential", 0], ["Industrial", 0]]}
      />

      <div className="grid gap-4 md:grid-cols-2">
        <LineChart title="Energy Consumption" />
        <Map />
      </div>

      <InsightsSection />

      <ActionToggle />
    </div>
  );
}

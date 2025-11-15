import { useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { ModeToggle } from "../components/ModeToggle";
import { DescriptionSection } from "../components/DescriptionSection";
import { Table } from "../components/Table";
import { Histogram } from "../components/Histogram";
import { Map } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { ActionToggle } from "../components/ActionToggle";

export function TrafficPage() {
  const [mode, setMode] = useState<"REAL" | "SIMULATE">("REAL");

  return (
    <div className="space-y-4 pb-16">
      <div className="flex items-center justify-between">
        <AreaBadge name="Nairobi" />
        <ModeToggle mode={mode} onChange={setMode} />
      </div>

      <DescriptionSection title="Traffic Description" />

      <Table
        columns={["Segment", "Flow"]}
        rows={[["Segment A", 0], ["Segment B", 0]]}
      />

      <div className="grid gap-4 md:grid-cols-2">
        <Histogram title="Traffic Volume" />
        <Map />
      </div>

      <InsightsSection />

      <ActionToggle />
    </div>
  );
}

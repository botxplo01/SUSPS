import { useEffect, useState } from "react";
import { AreaBadge } from "../components/AreaBadge";
import { DescriptionSection } from "../components/DescriptionSection";
import { LineChart } from "../components/LineChart";
import { BarChart } from "../components/BarChart";
import { Histogram } from "../components/Histogram";
import { HotspotMap } from "../components/Map";
import { InsightsSection } from "../components/InsightsSection";
import { FormattedInsights } from "../components/FormattedInsights";
import { ExportDialog } from "../components/ExportDialog";
import { postBinary, downloadBlob } from "../api";
import type {
  Area,
  ExportPayload,
  ExportPage,
  ExportFormat,
} from "../types";
import { useAdvisory } from "../hooks/useAdvisory";
import {
  useGrowthSeries,
  useEnergySeries,
  useTrafficSeries,
} from "../hooks/useSeries";

interface DashboardPageProps {
  selectedArea: Area | null;
  onRegisterExporter?: (fn: () => void) => void;
}

type DashboardExportTarget =
  | { kind: "page" }
  | { kind: "chart"; id: "growth" | "energy" | "traffic" };

const EXPORT_FOOTER_TEXT =
  "Smart Urban Simulation and Prediction System (SUSPS) — © 2025 Developed by David Lameck.";

export function DashboardPage({
  selectedArea,
  onRegisterExporter,
}: DashboardPageProps) {
  const zoneId = selectedArea ? selectedArea.name : null;
  const areaId = selectedArea ? selectedArea.id : null;
  const { insights, loading, error } = useAdvisory("dashboard", zoneId, "baseline");
  const { points: growthPoints } = useGrowthSeries(areaId);
  const { points: energyPoints } = useEnergySeries(areaId);
  const { points: trafficPoints } = useTrafficSeries(areaId);
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);
  const [exportTarget, setExportTarget] = useState<DashboardExportTarget | null>(
    null,
  );

  useEffect(() => {
    if (!onRegisterExporter) return;
    onRegisterExporter(() => {
      setExportTarget({ kind: "page" });
      setIsExportDialogOpen(true);
    });
  }, [onRegisterExporter]);

  const areaName = selectedArea?.name ?? "No area selected";
  const areaIdValue = selectedArea?.id ?? null;
  const insightsText =
    selectedArea && !loading && !error && insights ? insights : undefined;

  const buildGrowthPage = (): ExportPage => ({
    page_name: "Urban Growth",
    mode: "REAL",
    area_name: areaName,
    area_id: areaIdValue,
    description:
      selectedArea !== null
        ? `Urban Growth summary for ${selectedArea.name} in REAL mode.`
        : "Urban Growth summary in REAL mode.",
    insights: insightsText,
    tables: [
      {
        title: "Urban Growth Summary",
        columns: ["Year", "Population"],
        rows:
          growthPoints && growthPoints.length
            ? growthPoints.map((p) => [
                String(p.x),
                Math.round(p.y).toString(),
              ])
            : [["—", "—"]],
      },
    ],
    charts: [
      {
        title: "Urban Growth Summary",
        x_label: "Year",
        y_label: "Population",
        series: [
          {
            label: "Real",
            points: growthPoints ?? [],
          },
        ],
      },
    ],
  });

  const buildEnergyPage = (): ExportPage => ({
    page_name: "Energy",
    mode: "REAL",
    area_name: areaName,
    area_id: areaIdValue,
    description:
      selectedArea !== null
        ? `Energy summary for ${selectedArea.name} in REAL mode.`
        : "Energy summary in REAL mode.",
    insights: insightsText,
    tables: [
      {
        title: "Energy Summary",
        columns: ["Hour", "Demand (MWh)"],
        rows:
          energyPoints && energyPoints.length
            ? energyPoints.map((p) => [String(p.x), p.y.toFixed(2)])
            : [["—", "—"]],
      },
    ],
    charts: [
      {
        title: "Energy Summary",
        x_label: "Hour of day",
        y_label: "Demand (MWh)",
        series: [
          {
            label: "Real",
            points: energyPoints ?? [],
          },
        ],
      },
    ],
  });

  const buildTrafficPage = (): ExportPage => ({
    page_name: "Traffic",
    mode: "REAL",
    area_name: areaName,
    area_id: areaIdValue,
    description:
      selectedArea !== null
        ? `Traffic summary for ${selectedArea.name} in REAL mode.`
        : "Traffic summary in REAL mode.",
    insights: insightsText,
    tables: [
      {
        title: "Traffic Summary",
        columns: ["Hour", "Volume (veh/hr)"],
        rows:
          trafficPoints && trafficPoints.length
            ? trafficPoints.map((p) => [
                String(p.x),
                Math.round(p.y).toString(),
              ])
            : [["—", "—"]],
      },
    ],
    charts: [
      {
        title: "Traffic Summary",
        x_label: "Hour of day",
        y_label: "Volume (veh/hr)",
        series: [
          {
            label: "Real",
            points: trafficPoints ?? [],
          },
        ],
      },
    ],
  });

  const buildPagesForTarget = (target: DashboardExportTarget): ExportPage[] => {
    const allPages = [buildGrowthPage(), buildEnergyPage(), buildTrafficPage()];
    if (target.kind === "page") {
      return allPages;
    }
    if (target.id === "growth") return [allPages[0]];
    if (target.id === "energy") return [allPages[1]];
    return [allPages[2]];
  };

  const handleConfirmExport = async (format: ExportFormat) => {
    if (!exportTarget) return;
    const pages = buildPagesForTarget(exportTarget);
    const payload: ExportPayload = {
      export_format: format,
      pages,
      footer_text: EXPORT_FOOTER_TEXT,
    };

    try {
      const blob = await postBinary("/export", payload);
      const areaNameFragment = selectedArea?.name
        ? ` - ${selectedArea.name}`
        : "";
      const baseName =
        exportTarget.kind === "page"
          ? `SUSPS - Dashboard${areaNameFragment}`
          : exportTarget.id === "growth"
          ? `SUSPS - Dashboard - Urban Growth chart${areaNameFragment}`
          : exportTarget.id === "energy"
          ? `SUSPS - Dashboard - Energy chart${areaNameFragment}`
          : `SUSPS - Dashboard - Traffic chart${areaNameFragment}`;
      const ext = format === "pdf" ? ".pdf" : format === "csv" ? ".csv" : ".zip";
      downloadBlob(blob, `${baseName}${ext}`);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("Failed to export Dashboard data", err);
    }
  };

  const handleOpenGrowthChartExport = () => {
    setExportTarget({ kind: "chart", id: "growth" });
    setIsExportDialogOpen(true);
  };

  const handleOpenEnergyChartExport = () => {
    setExportTarget({ kind: "chart", id: "energy" });
    setIsExportDialogOpen(true);
  };

  const handleOpenTrafficChartExport = () => {
    setExportTarget({ kind: "chart", id: "traffic" });
    setIsExportDialogOpen(true);
  };

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
          onExport={handleOpenGrowthChartExport}
        />
        <LineChart
          title="Energy Summary"
          data={energyPoints}
          accentColor="#f87b14"
          xLabel="Hour of day"
          yLabel="Demand (MWh)"
          onExport={handleOpenEnergyChartExport}
        />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Histogram
          title="Traffic Summary"
          data={trafficPoints}
          accentColor="#f24152"
          xLabel="Hour of day"
          yLabel="Volume (veh/hr)"
          onExport={handleOpenTrafficChartExport}
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

      <ExportDialog
        isOpen={isExportDialogOpen}
        onClose={() => {
          setIsExportDialogOpen(false);
          setExportTarget(null);
        }}
        onConfirm={(format) => {
          void handleConfirmExport(format);
        }}
      />
    </div>
  );
}

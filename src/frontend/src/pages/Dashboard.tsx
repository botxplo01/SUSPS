// @author: Lameck David Musumpuka

import { useEffect, useState, useRef } from "react";
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
  ChartExportHandle,
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

/** Footer text used for Dashboard PDF/CSV exports. */
const EXPORT_FOOTER_TEXT =
  "Smart Urban Simulation and Prediction System (SUSPS) — © 2025 Developed by David Lameck.";

/**
 * Area-driven dashboard page.
 *
 * Shows baseline growth, energy, and traffic summaries plus a hotspot map
 * and AI advisory for the selected area. Also coordinates holistic and
 * per-chart export flows.
 */
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
  const growthChartRef = useRef<ChartExportHandle | null>(null);
  const energyChartRef = useRef<ChartExportHandle | null>(null);
  const trafficChartRef = useRef<ChartExportHandle | null>(null);
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

  const buildGrowthPage = (growthImage?: string | null): ExportPage => ({
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
        image_data: growthImage ?? undefined,
      },
    ],
  });

  const buildEnergyPage = (energyImage?: string | null): ExportPage => ({
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
        image_data: energyImage ?? undefined,
      },
    ],
  });

  const buildTrafficPage = (trafficImage?: string | null): ExportPage => ({
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
        image_data: trafficImage ?? undefined,
      },
    ],
  });

  const buildPagesForTarget = (
    target: DashboardExportTarget,
    images: { growth?: string | null; energy?: string | null; traffic?: string | null },
  ): ExportPage[] => {
    const growthPage = buildGrowthPage(images.growth);
    const energyPage = buildEnergyPage(images.energy);
    const trafficPage = buildTrafficPage(images.traffic);
    const allPages = [growthPage, energyPage, trafficPage];

    // Holistic export from the Dashboard header: prepend a dedicated Dashboard
    // page that carries the AI Analysis & Insights section, then follow with the
    // domain-specific pages. The backend will render the insights only once at
    // the top of the document (first page).
    if (target.kind === "page") {
      const dashboardDescription = selectedArea
        ? `Dashboard overview for ${selectedArea.name} in REAL mode across growth, energy, and traffic.`
        : "Dashboard overview in REAL mode across growth, energy, and traffic.";

      const dashboardPage: ExportPage = {
        page_name: "Dashboard",
        mode: "REAL",
        area_name: areaName,
        area_id: areaIdValue,
        description: dashboardDescription,
        insights: insightsText,
        tables: [],
        charts: [],
      };

      // Strip insights from the domain pages in the holistic export so AI
      // Analysis & Insights is shown only once at the top of the document.
      const pagesWithoutInsights = allPages.map((p) => ({ ...p, insights: undefined }));
      return [dashboardPage, ...pagesWithoutInsights];
    }

    // Single-chart exports from the Dashboard still include the dashboard-level
    // advisory on the single page.
    if (target.id === "growth") return [growthPage];
    if (target.id === "energy") return [energyPage];
    return [trafficPage];
  };

  const handleConfirmExport = async (format: ExportFormat) => {
    if (!exportTarget) return;

    const growthImage = growthChartRef.current
      ? await growthChartRef.current.capturePng()
      : null;
    const energyImage = energyChartRef.current
      ? await energyChartRef.current.capturePng()
      : null;
    const trafficImage = trafficChartRef.current
      ? await trafficChartRef.current.capturePng()
      : null;

    const pages = buildPagesForTarget(exportTarget, {
      growth: growthImage,
      energy: energyImage,
      traffic: trafficImage,
    });
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
          ref={growthChartRef}
          title="Urban Growth Summary"
          data={growthPoints}
          accentColor="#91e03f"
          xLabel="Year"
          yLabel="Population"
          onExport={handleOpenGrowthChartExport}
        />
        <LineChart
          ref={energyChartRef}
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
          ref={trafficChartRef}
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

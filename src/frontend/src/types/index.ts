export type Mode = "REAL" | "SIMULATE";

export interface Area {
  id: number;
  name: string;
  type?: string;
}

export interface ChartPoint {
  x: number;
  y: number;
}

export interface ChartSeries {
  label: string;
  color: string;
  points: ChartPoint[];
}

export interface HotspotArea {
  admin_unit: string;
  population?: number;
  pop_share?: number;
  income_norm?: number;
  employment_score?: number;
  hotspot_score?: number;
}

export interface HotspotForecastArea extends HotspotArea {
  year: number;
}

// Export payload types for /export endpoint
export type ExportFormat = "pdf" | "csv" | "bundle";

export interface ExportChartSeries {
  label: string;
  points: ChartPoint[];
}

export interface ExportChart {
  title: string;
  x_label?: string;
  y_label?: string;
  series: ExportChartSeries[];
}

export interface ExportTable {
  title: string;
  columns: string[];
  rows: (string | null)[][];
}

export interface ExportPage {
  page_name: string;
  mode: Mode;
  area_name: string;
  area_id?: number | null;
  description?: string;
  insights?: string;
  tables: ExportTable[];
  charts: ExportChart[];
}

export interface ExportPayload {
  export_format: ExportFormat;
  pages: ExportPage[];
  footer_text?: string;
}

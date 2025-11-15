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

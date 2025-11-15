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

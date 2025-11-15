import type { ChartPoint } from "../types";

interface LineChartProps {
  title?: string;
  data?: ChartPoint[];
}

export function LineChart({ title, data }: LineChartProps) {
  const points = data ?? [];
  const max = points.reduce((m, p) => (p.y > m ? p.y : m), 0);
  const safeMax = max > 0 ? max : 1;

  const pathD = (() => {
    if (points.length === 0) return "";
    return points
      .map((p, idx) => {
        const x = (idx / Math.max(points.length - 1, 1)) * 100;
        const y = 40 - (p.y / safeMax) * 35;
        return `${idx === 0 ? "M" : "L"}${x},${y}`;
      })
      .join(" ");
  })();

  return (
    <section className="rounded-xl bg-white p-4 shadow-sm">
      {title && <h2 className="mb-2 text-sm font-semibold text-gray-800">{title}</h2>}
      {points.length === 0 ? (
        <div className="flex h-40 items-center justify-center text-xs text-gray-500">
          No data available.
        </div>
      ) : (
        <div className="h-40 w-full">
          <svg viewBox="0 0 100 40" preserveAspectRatio="none" className="h-full w-full">
            <path
              d={pathD}
              fill="none"
              className="stroke-neutral-800"
              strokeWidth={1.5}
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          </svg>
        </div>
      )}
    </section>
  );
}

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
      {title && (
        <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-800">
          <span className="inline-flex h-5 w-5 items-center justify-center rounded bg-[#62d9c5]/10">
            <span className="h-0.5 w-3 rounded-full bg-[#62d9c5]" />
          </span>
          <span>{title}</span>
        </h2>
      )}
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
              className="stroke-[#62d9c5]"
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

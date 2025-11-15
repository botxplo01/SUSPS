import type { ChartPoint } from "../types";

interface BarChartProps {
  title?: string;
  data?: ChartPoint[];
}

export function BarChart({ title, data }: BarChartProps) {
  const points = data ?? [];
  const max = points.reduce((m, p) => (p.y > m ? p.y : m), 0);
  const safeMax = max > 0 ? max : 1;

  return (
    <section className="rounded-xl bg-white p-4 shadow-sm">
      {title && (
        <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-800">
          <span className="inline-flex h-5 w-5 items-center justify-center rounded bg-[#62d9c5]/10">
            <span className="h-2.5 w-2.5 rounded-sm bg-[#62d9c5]" />
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
            {points.map((p, idx) => {
              const barWidth = 100 / (points.length * 1.5);
              const spacing = 100 / points.length;
              const x = idx * spacing + spacing / 2 - barWidth / 2;
              const height = (p.y / safeMax) * 35;
              const y = 40 - height;
              return (
                <rect
                  key={idx}
                  x={x}
                  y={y}
                  width={barWidth}
                  height={height}
                  rx={1.5}
                  className="fill-[#62d9c5]"
                />
              );
            })}
          </svg>
        </div>
      )}
    </section>
  );
}

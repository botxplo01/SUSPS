import type { ChartPoint, ChartSeries } from "../types";

interface LineChartProps {
  title?: string;
  data?: ChartPoint[];
  series?: ChartSeries[];
  accentColor?: string;
  xLabel?: string;
  yLabel?: string;
  showGrid?: boolean;
}

export function LineChart({
  title,
  data,
  series,
  accentColor = "#62d9c5",
  xLabel,
  yLabel,
  showGrid = true,
}: LineChartProps) {
  const singlePoints = data ?? [];
  const hasSeries = !!series && series.length > 0;
  const primarySeries: ChartSeries | null = hasSeries
    ? series![0]
    : {
        label: title ?? "Series",
        color: accentColor,
        points: singlePoints,
      };
  const seriesList: ChartSeries[] = hasSeries ? series! : [primarySeries];
  const points = primarySeries.points ?? [];
  const allPoints = seriesList.flatMap((s) => s.points ?? []);
  const max = allPoints.reduce((m, p) => (p.y > m ? p.y : m), 0);
  const safeMax = max > 0 ? max : 1;

  const viewBoxWidth = 100;
  const viewBoxHeight = 40;
  const margin = { top: 4, right: 4, bottom: 10, left: 16 };
  const innerWidth = viewBoxWidth - margin.left - margin.right;
  const innerHeight = viewBoxHeight - margin.top - margin.bottom;

  const buildPathD = (pts: ChartPoint[]): string => {
    if (!pts.length) return "";
    return pts
      .map((p, idx) => {
        const x =
          margin.left +
          (idx / Math.max(points.length - 1, 1)) * innerWidth;
        const y =
          margin.top +
          innerHeight -
          (p.y / safeMax) * innerHeight;
        return `${idx === 0 ? "M" : "L"}${x},${y}`;
      })
      .join(" ");
  };

  const yTicks = 4;
  const yTickValues = Array.from({ length: yTicks }, (_, i) =>
    (safeMax * i) / (yTicks - 1),
  );

  const formatTick = (value: number) => {
    if (value === 0) return "0";
    if (safeMax >= 10) return value.toFixed(0);
    return value.toFixed(1);
  };

  const xTickIndices = (() => {
    if (points.length === 0) return [] as number[];
    const maxXTicks = Math.min(points.length, 6);
    if (points.length <= maxXTicks) {
      return points.map((_, idx) => idx);
    }
    const indices: number[] = [];
    for (let i = 0; i < maxXTicks; i += 1) {
      const rawIndex = Math.round(
        (i / (maxXTicks - 1)) * (points.length - 1),
      );
      if (!indices.includes(rawIndex)) {
        indices.push(rawIndex);
      }
    }
    return indices;
  })();

  return (
    <section className="flex flex-col rounded-xl bg-white p-4 shadow-sm">
      {title && (
        <div className="mb-2 flex items-center justify-between gap-2 text-sm font-semibold text-gray-800">
          <span>{title}</span>
          <div className="flex flex-wrap gap-2 text-[11px] font-normal text-gray-700">
            {seriesList.map((s) => (
              <span key={s.label} className="inline-flex items-center gap-1">
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: s.color }}
                />
                <span>{s.label}</span>
              </span>
            ))}
          </div>
        </div>
      )}
      {points.length === 0 ? (
        <div className="flex min-h-[160px] flex-1 items-center justify-center text-xs text-gray-500">
          No data available.
        </div>
      ) : (
        <div className="flex min-h-[160px] flex-1 items-center justify-center">
          <svg
            viewBox={`0 0 ${viewBoxWidth} ${viewBoxHeight}`}
            preserveAspectRatio="xMidYMid meet"
            className="w-full max-h-full"
          >
            {/* Y-axis gridlines and labels */}
            {showGrid &&
              yTickValues.map((value, idx) => {
                const y =
                  margin.top +
                  innerHeight -
                  (value / safeMax) * innerHeight;
                return (
                  <g key={idx}>
                    <line
                      x1={margin.left}
                      y1={y}
                      x2={margin.left + innerWidth}
                      y2={y}
                      stroke="#e5e7eb"
                      strokeWidth={0.4}
                    />
                    <text
                      x={margin.left - 1.5}
                      y={y}
                      textAnchor="end"
                      alignmentBaseline="middle"
                      fontSize={2.5}
                      fill="#6b7280"
                    >
                      {formatTick(value)}
                    </text>
                  </g>
                );
              })}

            {/* Axes */}
            <line
              x1={margin.left}
              y1={margin.top}
              x2={margin.left}
              y2={margin.top + innerHeight}
              stroke="#9ca3af"
              strokeWidth={0.6}
            />
            <line
              x1={margin.left}
              y1={margin.top + innerHeight}
              x2={margin.left + innerWidth}
              y2={margin.top + innerHeight}
              stroke="#9ca3af"
              strokeWidth={0.6}
            />

            {/* Line paths for each series */}
            {seriesList.map((s) => (
              <path
                key={s.label}
                d={buildPathD(s.points)}
                fill="none"
                stroke={s.color}
                strokeWidth={1.5}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            ))}

            {/* X-axis tick labels */}
            {xTickIndices.map((idx) => {
              const x =
                margin.left +
                (idx / Math.max(points.length - 1, 1)) * innerWidth;
              const label = points[idx]?.x;
              return (
                <text
                  key={idx}
                  x={x}
                  y={margin.top + innerHeight + 4}
                  textAnchor="middle"
                  alignmentBaseline="hanging"
                  fontSize={2.5}
                  fill="#6b7280"
                >
                  {label}
                </text>
              );
            })}

            {/* Axis labels */}
            {yLabel && (
              <text
                x={margin.left - 10}
                y={margin.top + innerHeight / 2}
                textAnchor="middle"
                alignmentBaseline="middle"
                fontSize={3}
                fill="#4b5563"
                transform={`rotate(-90 ${margin.left - 10} ${
                  margin.top + innerHeight / 2
                })`}
              >
                {yLabel}
              </text>
            )}
            {xLabel && (
              <text
                x={margin.left + innerWidth / 2}
                y={viewBoxHeight - 1}
                textAnchor="middle"
                alignmentBaseline="baseline"
                fontSize={3}
                fill="#4b5563"
              >
                {xLabel}
              </text>
            )}
          </svg>
        </div>
      )}
    </section>
  );
}

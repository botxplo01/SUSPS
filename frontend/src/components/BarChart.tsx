/** @author: David Lameck **/

import { forwardRef, useImperativeHandle, useRef } from "react";
import type { ChartPoint, ChartSeries, ChartExportHandle } from "../types";

/**
 * SVG-based bar chart that supports multiple overlaid series.
 *
 * Exposes an imperative handle so pages can capture the chart as a PNG for
 * inclusion in PDF exports.
 */
interface BarChartProps {
  title?: string;
  data?: ChartPoint[];
  series?: ChartSeries[];
  accentColor?: string;
  xLabel?: string;
  yLabel?: string;
  showGrid?: boolean;
  onExport?: () => void;
}

export const BarChart = forwardRef<ChartExportHandle, BarChartProps>(
  function BarChart(
    {
      title,
      data,
      series,
      accentColor = "#62d9c5",
      xLabel,
      yLabel,
      showGrid = true,
      onExport,
    }: BarChartProps,
    ref,
  ) {
    const svgRef = useRef<SVGSVGElement | null>(null);

    const captureSvgAsPng = async (): Promise<string | null> => {
      if (typeof document === "undefined") return null;
      const svg = svgRef.current;
      if (!svg) return null;

      try {
        const xml = new XMLSerializer().serializeToString(svg);
        const blob = new Blob([xml], {
          type: "image/svg+xml;charset=utf-8",
        });
        const url = URL.createObjectURL(blob);
        const img = new Image();
        const width = svg.clientWidth || 800;
        const height = svg.clientHeight || 400;
        const dpr = window.devicePixelRatio || 1;
        const canvas = document.createElement("canvas");
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        const ctx = canvas.getContext("2d");
        if (!ctx) {
          URL.revokeObjectURL(url);
          return null;
        }
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        img.crossOrigin = "anonymous";

        const dataUrl: string | null = await new Promise((resolve) => {
          img.onload = () => {
            ctx.clearRect(0, 0, width, height);
            ctx.drawImage(img, 0, 0, width, height);
            URL.revokeObjectURL(url);
            try {
              resolve(canvas.toDataURL("image/png"));
            } catch {
              resolve(null);
            }
          };
          img.onerror = () => {
            URL.revokeObjectURL(url);
            resolve(null);
          };
          img.src = url;
        });

        return dataUrl;
      } catch {
        return null;
      }
    };

    useImperativeHandle(
      ref,
      () => ({
        capturePng: captureSvgAsPng,
      }),
      [],
    );

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

    const seriesCount = seriesList.length || 1;
    const spacing = points.length > 0 ? innerWidth / points.length : 0;
    const groupWidth = spacing * 0.8;
    const barWidth = seriesCount > 0 ? groupWidth / seriesCount : 0;

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
      <section className="relative flex flex-col rounded-xl bg-white p-4 shadow-sm">
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
            ref={svgRef}
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

            {/* Bars for each series, grouped by x position */}
            {points.map((p, idx) => {
              const groupStart =
                margin.left + idx * spacing + spacing / 2 - groupWidth / 2;
              return seriesList.map((s, sIdx) => {
                const val = s.points[idx]?.y ?? 0;
                const height = (val / safeMax) * innerHeight;
                const y = margin.top + innerHeight - height;
                const x = groupStart + sIdx * barWidth;
                return (
                  <rect
                    key={`${s.label}-${idx}`}
                    x={x}
                    y={y}
                    width={barWidth}
                    height={height}
                    rx={1.5}
                    fill={s.color}
                  />
                );
              });
            })}

            {/* X-axis tick labels */}
            {xTickIndices.map((idx) => {
              const x =
                margin.left + idx * spacing + spacing / 2;
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
      {onExport && (
        <button
          type="button"
          onClick={onExport}
          className="absolute bottom-3 right-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-blue-900 text-white shadow-sm hover:bg-blue-800"
          aria-label="Export chart"
        >
          <svg viewBox="0 0 20 20" className="h-4 w-4" aria-hidden="true">
            <path
              d="M10 2a.75.75 0 01.75.75v7.19l2.22-2.22a.75.75 0 111.06 1.06l-3.5 3.5a.75.75 0 01-1.06 0l-3.5-3.5a.75.75 0 111.06-1.06l2.22 2.22V2.75A.75.75 0 0110 2z"
              className="fill-current"
            />
            <path
              d="M4 12.75a.75.75 0 011.5 0v1.5h9v-1.5a.75.75 0 011.5 0v2.25A1.25 1.25 0 0114.75 16H5.25A1.25 1.25 0 014 15.25z"
              className="fill-current"
            />
          </svg>
        </button>
      )}
    </section>
  );
});


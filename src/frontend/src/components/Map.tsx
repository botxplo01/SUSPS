import { useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip } from "react-leaflet";
import type { LatLngExpression } from "leaflet";
import { useHotspotAreas, useHotspotForecast } from "../hooks/useHotspots";

// Default centre and zoom reflect the Nairobi CBD as per the SUSPS spec.
const DEFAULT_CENTER: LatLngExpression = [-1.286389, 36.817223];
const DEFAULT_ZOOM = 12;
// Threshold for treating a forecast hotspot score as an "improvement" zone.
const MIN_IMPROVEMENT = 0.05;

interface MapProps {
  optimize?: boolean;
  zoneId?: string | null;
}

/**
 * Leaflet-based hotspot map.
 *
 * Renders current and forecast hotspot scores as soft circles around a
 * city centre, highlighting improving areas in green when Optimize is
 * active. Uses a simple radial layout until full GeoJSON joins are added.
 */
export function HotspotMap({ optimize = false, zoneId }: MapProps) {
  const [yearOffset, setYearOffset] = useState<number>(0);
  const { items: baseAreas, loading: baseLoading, error: baseError } =
    useHotspotAreas(zoneId);
  const { items: forecastAreas, loading: forecastLoading } =
    useHotspotForecast(undefined, zoneId);

  // Derive currentYear and per-year forecast without extra hooks to avoid
  // any potential hooks-order issues when React re-renders in StrictMode.
  let currentYear: number | undefined = undefined;
  if (forecastAreas.length > 0) {
    const years = forecastAreas
      .map((a) => a.year)
      .filter((y) => Number.isFinite(y));
    if (years.length > 0) {
      const min = Math.min(...years);
      const max = Math.max(...years);
      const clampedOffset = Math.max(0, Math.min(yearOffset, max - min));
      currentYear = min + clampedOffset;
    }
  }

  const forecastForYear = currentYear
    ? forecastAreas.filter((a) => a.year === currentYear)
    : [];

  const topCurrent = [...baseAreas]
    .filter((a) => (a.hotspot_score ?? 0) > 0)
    .sort((a, b) => (b.hotspot_score ?? 0) - (a.hotspot_score ?? 0))
    .slice(0, 6)
    .sort((a, b) => a.admin_unit.localeCompare(b.admin_unit));

  const topFuture = [...forecastForYear]
    .filter((a) => (a.hotspot_score ?? 0) > 0)
    .sort((a, b) => (b.hotspot_score ?? 0) - (a.hotspot_score ?? 0))
    .slice(0, 6)
    .sort((a, b) => a.admin_unit.localeCompare(b.admin_unit));

  const optimalZones = (() => {
    if (!forecastForYear.length || !baseAreas.length) return [] as {
      admin_unit: string;
      baseScore: number;
      futureScore: number;
      improvement: number;
    }[];
    const baseByUnit = new Map(baseAreas.map((a) => [a.admin_unit, a] as const));
    return forecastForYear
      .map((future) => {
        const base = baseByUnit.get(future.admin_unit);
        const baseScore = base?.hotspot_score ?? 0;
        const futureScore = future.hotspot_score ?? 0;
        const improvement = baseScore - futureScore;
        return {
          admin_unit: future.admin_unit,
          baseScore,
          futureScore,
          improvement,
        };
      })
      .filter(
        (z) =>
          z.baseScore > 0.1 && z.futureScore > 0 && z.improvement >= MIN_IMPROVEMENT,
      )
      .sort((a, b) => b.improvement - a.improvement)
      .slice(0, 5);
  })();

  const sortZonesByName = (zones: { admin_unit: string }[]) =>
    zones.slice().sort((a, b) => a.admin_unit.localeCompare(b.admin_unit));

  const filteredOptimalZones = (() => {
    if (!zoneId) return sortZonesByName(optimalZones);
    const target = zoneId.toLowerCase();
    const exact = optimalZones.filter((z) => z.admin_unit.toLowerCase() === target);
    if (exact.length > 0) return sortZonesByName(exact);
    const partial = optimalZones.filter((z) =>
      z.admin_unit.toLowerCase().includes(target),
    );
    return partial.length > 0 ? sortZonesByName(partial) : sortZonesByName(optimalZones);
  })();

  const isLoading = baseLoading || forecastLoading;

  // Simple fan-out layout of markers around the city center until true
  // GeoJSON-based joins are wired, in line with instructions.md.
  const markerPositions: LatLngExpression[] = (() => {
    const count = Math.max(topCurrent.length, topFuture.length);
    if (!count) return [];
    const [lat, lng] = DEFAULT_CENTER as [number, number];
    const radius = 0.02; // ~2km at equator
    return Array.from({ length: count }, (_, idx) => {
      const angle = (2 * Math.PI * idx) / count;
      return [
        lat + radius * Math.cos(angle),
        lng + radius * Math.sin(angle),
      ] as LatLngExpression;
    });
  })();

  const hasSelection = !!zoneId;

  if (!hasSelection) {
    return (
      <section className="rounded-xl bg-white p-4 shadow-sm">
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-800">
            Hotspot Map (current vs forecast)
          </h2>
        </div>
        <div className="flex h-80 items-center justify-center text-xs text-gray-500">
          No data available.
        </div>
        <p className="mt-3 text-[11px] text-gray-500">
          This panel summarizes current and forecasted hotspot scores by
          administrative unit on top of live OpenStreetMap tiles. Areas with
          dense population pressure, congestion, and inefficient energy use
          appear as red circles. When Optimize is active, zones whose forecast
          scores improve are highlighted in green as potential optimal zones. In
          a later iteration, these scores can be joined with ward/zone GeoJSON
          or Overpass-derived polygons to render a full choropleth map.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-xl bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-800">
          Hotspot Map (current vs forecast)
        </h2>
        {currentYear && (
          <div className="flex items-center gap-2 text-[11px] text-gray-500">
            <span>Year offset</span>
            <input
              type="range"
              min={0}
              max={3}
              step={1}
              value={yearOffset}
              onChange={(e) => setYearOffset(Number(e.target.value) || 0)}
              className="h-1 w-20 cursor-pointer appearance-none rounded-full bg-neutral-200"
            />
          </div>
        )}
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="relative h-80 overflow-hidden rounded-lg shadow-inner">
          <MapContainer
            center={DEFAULT_CENTER}
            zoom={DEFAULT_ZOOM}
            className="h-full w-full"
            scrollWheelZoom={false}
            attributionControl={false}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution="&copy; OpenStreetMap contributors"
            />
            {markerPositions.map((pos, idx) => {
              const base = topCurrent[idx];
              const future = topFuture[idx];
              const baseScore = base?.hotspot_score ?? 0;
              const futureScore = future?.hotspot_score ?? 0;
              const effectiveScore = baseScore || futureScore;
              const radius = 10 + effectiveScore * 20;

              // Hotspots (dense population, congestion, inefficient energy) are soft red.
              // Spots where the forecast hotspot score improves are treated as "optimal"
              // candidates. These are only highlighted in green when Optimize is active.
              const isImproving = future && base && futureScore < baseScore;
              const isOptimal = optimize && isImproving;
              const color = isOptimal ? "#22c55e" : "#ef4444"; // green vs red
              const fillOpacity = 0.35;

              const label = base?.admin_unit || future?.admin_unit || `Area ${idx + 1}`;
              if (!base && !future) return null;
              return (
                <CircleMarker
                  key={idx}
                  center={pos}
                  radius={radius}
                  pathOptions={{ color, fillColor: color, fillOpacity }}
                >
                  <Tooltip direction="top" offset={[0, -4]}>
                    <div className="text-xs">
                      <div className="font-semibold">{label}</div>
                      {baseScore ? (
                        <div>Current hotspot: {(baseScore * 100).toFixed(0)}%</div>
                      ) : null}
                      {futureScore ? (
                        <div>Forecast hotspot: {(futureScore * 100).toFixed(0)}%</div>
                      ) : null}
                      {isOptimal && (
                        <div className="mt-0.5 text-[11px] text-emerald-200">
                          Potential optimal zone (improving risk)
                        </div>
                      )}
                    </div>
                  </Tooltip>
                </CircleMarker>
              );
            })}
          </MapContainer>
          <div className="pointer-events-none absolute inset-x-0 bottom-1 flex justify-between px-3 text-[9px] text-gray-200 drop-shadow-sm">
            <span>OSM base map</span>
            <span>Circles show relative hotspot intensity</span>
          </div>
        </div>

        <div className="space-y-2 text-xs">
          <div>
            <h3 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-gray-600">
              Current hotspots
            </h3>
            <ul className="space-y-1">
              {topCurrent.map((a) => (
                <li key={a.admin_unit} className="flex items-center justify-between">
                  <span className="truncate pr-2 text-gray-800">
                    {a.admin_unit}
                  </span>
                  <div className="flex items-center gap-1">
                    <div className="h-1.5 w-16 overflow-hidden rounded-full bg-neutral-200">
                      <div
                        className="h-full rounded-full bg-red-500"
                        style={{ width: `${Math.max(5, (a.hotspot_score ?? 0) * 100)}%` }}
                      />
                    </div>
                    <span className="w-10 text-right text-[10px] text-gray-500">
                      {((a.hotspot_score ?? 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                </li>
              ))}
              {!isLoading && topCurrent.length === 0 && (
                <li className="text-[11px] text-gray-500">No hotspot data.</li>
              )}
            </ul>
          </div>

          <div>
            <h3 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-gray-600">
              Forecast hotspots{currentYear ? ` (${currentYear})` : ""}
            </h3>
            <ul className="space-y-1">
              {topFuture.map((a) => (
                <li key={`${a.admin_unit}-${a.year}`} className="flex items-center justify-between">
                  <span className="truncate pr-2 text-gray-800">
                    {a.admin_unit}
                  </span>
                  <div className="flex items-center gap-1">
                    <div className="h-1.5 w-16 overflow-hidden rounded-full bg-neutral-200">
                      <div
                        className="h-full rounded-full bg-amber-500"
                        style={{ width: `${Math.max(5, (a.hotspot_score ?? 0) * 100)}%` }}
                      />
                    </div>
                    <span className="w-10 text-right text-[10px] text-gray-500">
                      {((a.hotspot_score ?? 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                </li>
              ))}
              {!isLoading && topFuture.length === 0 && (
                <li className="text-[11px] text-gray-500">
                  No forecast hotspot data.
                </li>
              )}
            </ul>
          </div>

          <div>
            <h3 className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-gray-600">
              Optimal zones
            </h3>
            <ul className="space-y-1">
              {optimize ? (
                filteredOptimalZones.length > 0 ? (
                  filteredOptimalZones.map((z) => (
                    <li
                      key={z.admin_unit}
                      className="flex items-center justify-between"
                    >
                      <span className="truncate pr-2 text-gray-800">
                        {z.admin_unit}
                      </span>
                      <div className="flex items-center gap-1">
                        <span className="text-[10px] text-gray-500">
                          {(z.baseScore * 100).toFixed(0)}% →
                        </span>
                        <span className="text-[10px] font-semibold text-emerald-600">
                          {(z.futureScore * 100).toFixed(0)}%
                        </span>
                      </div>
                    </li>
                  ))
                ) : (
                  <li className="text-[11px] text-gray-500">
                    No optimal zones identified for this forecast year.
                  </li>
                )
              ) : (
                <li className="text-[11px] text-gray-500">
                  Toggle Optimize to highlight improving zones in green on the map
                  and surface them here.
                </li>
              )}
            </ul>
          </div>

          {baseError && (
            <p className="text-[11px] text-red-600">{baseError}</p>
          )}
        </div>
      </div>

      <p className="mt-3 text-[11px] text-gray-500">
        This panel summarizes current and forecasted hotspot scores by
        administrative unit on top of live OpenStreetMap tiles. Areas with dense
        population pressure, congestion, and inefficient energy use appear as
        red circles. When Optimize is active, zones whose forecast scores
        improve are highlighted in green as potential optimal zones. In a later
        iteration, these scores can be joined with ward/zone GeoJSON or
        Overpass-derived polygons to render a full choropleth map.
      </p>
    </section>
  );
}

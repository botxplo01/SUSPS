import { useEffect, useMemo, useState } from "react";
import { NavLink } from "react-router-dom";
import type { Area } from "../types";
import { fetchJson } from "../api";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/urban-growth", label: "Urban Growth" },
  { to: "/energy", label: "Energy" },
  { to: "/traffic", label: "Traffic" },
];

interface SidebarProps {
  selectedArea: Area | null;
  onSelectArea: (area: Area) => void;
}

export function Sidebar({ selectedArea, onSelectArea }: SidebarProps) {
  const [areas, setAreas] = useState<Area[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchJson<{ items: any[] }>("/areas")
      .then((data) => {
        if (cancelled) return;
        const mapped: Area[] = (data.items ?? []).map((item, idx) => ({
          id: item.area_id ?? item.id ?? idx + 1,
          name: item.name ?? "Area",
          type: item.area_type,
        }));
        setAreas(mapped);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof Error ? err.message : "Failed to load areas from API.",
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const suggestions = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return areas;
    return areas.filter((a) => a.name.toLowerCase().includes(q));
  }, [areas, query]);

  return (
    <aside className="flex w-64 flex-col bg-sidebar text-gray-100">
      <div className="px-4 pb-2 pt-6 text-2xl font-semibold">SUSPS</div>
      <div className="px-4 pb-4">
        <input
          type="text"
          placeholder="Search area..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-md bg-neutral-800 px-3 py-2 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
        />
        <div className="mt-2 max-h-40 space-y-1 overflow-y-auto text-xs">
          {loading && <p className="text-gray-300">Loading areas...</p>}
          {error && <p className="text-red-300">{error}</p>}
          {!loading && !error && suggestions.length === 0 && (
            <p className="text-gray-300">No results.</p>
          )}
          {!loading && !error &&
            suggestions.map((area) => (
              <button
                key={area.id}
                type="button"
                onClick={() => {
                  onSelectArea(area);
                  setQuery("");
                }}
                className={`flex w-full items-center justify-between rounded-md px-2 py-1 text-left hover:bg-neutral-700 ${
                  selectedArea && selectedArea.id === area.id
                    ? "bg-neutral-700 font-semibold"
                    : ""
                }`}
              >
                <span>{area.name}</span>
                {area.type && (
                  <span className="text-[10px] uppercase text-gray-300">
                    {area.type}
                  </span>
                )}
              </button>
            ))}
        </div>
      </div>
      <nav className="mt-2 flex-1 space-y-1 px-2 pb-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `block rounded-md px-3 py-2 text-sm font-medium transition ${
                isActive ? "bg-gray-100 text-black" : "text-gray-200 hover:bg-neutral-700"
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

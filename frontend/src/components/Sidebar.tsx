/** @author: David Lameck **/

import { useEffect, useMemo, useState } from "react";
import { NavLink } from "react-router-dom";
import type { Area } from "../types";
import { fetchJson } from "../api";

const navItems = [
  {
    to: "/dashboard",
    label: "Dashboard",
    borderClass: "border-[#62d9c5]",
    iconActiveClass: "border-[#62d9c5] bg-[#62d9c5]/20",
  },
  {
    to: "/urban-growth",
    label: "Urban Growth",
    borderClass: "border-[#8cff47]",
    iconActiveClass: "border-[#8cff47] bg-[#8cff47]/20",
  },
  {
    to: "/energy",
    label: "Energy",
    borderClass: "border-[#ff9d14]",
    iconActiveClass: "border-[#ff9d14] bg-[#ff9d14]/20",
  },
  {
    to: "/traffic",
    label: "Traffic",
    borderClass: "border-[#ff4444]",
    iconActiveClass: "border-[#ff4444] bg-[#ff4444]/20",
  },
];

interface SidebarProps {
  selectedArea: Area | null;
  onSelectArea: (area: Area) => void;
  onResetArea: () => void;
  onUnloadArea: () => void;
  isMobileOpen: boolean;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export function Sidebar({
  selectedArea,
  onSelectArea,
  onResetArea,
  onUnloadArea,
  isMobileOpen,
  isCollapsed,
  onToggleCollapse,
}: SidebarProps) {
  const [areas, setAreas] = useState<Area[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSearchFocused, setIsSearchFocused] = useState(false);

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

    const scored = areas
      .map((area) => {
        const name = area.name.toLowerCase();
        const idx = name.indexOf(q);
        if (idx === -1) return null;
        return { area, idx, len: name.length };
      })
      .filter((item): item is { area: Area; idx: number; len: number } => item !== null)
      .sort((a, b) => {
        if (a.idx !== b.idx) return a.idx - b.idx; // prefix matches first
        return a.len - b.len; // then shorter names
      });

    return scored.map((s) => s.area);
  }, [areas, query]);

  const renderNavIcon = (path: string) => {
    if (path.startsWith("/dashboard")) {
      return (
        <svg
          viewBox="0 0 24 24"
          className="h-5 w-5"
          aria-hidden="true"
        >
          <path
            d="M3 10.5L12 4l9 6.5V20a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1v-9.5z"
            className="fill-current"
          />
        </svg>
      );
    }
    if (path.startsWith("/energy")) {
      return (
        <svg
          viewBox="0 0 24 24"
          className="h-5 w-5"
          aria-hidden="true"
        >
          <circle
            cx="12"
            cy="12"
            r="8.5"
            stroke="currentColor"
            strokeWidth="1.5"
            fill="none"
          />
          <path
            d="M11 5l-3 7h3v7l3-7h-3z"
            fill="white"
          />
        </svg>
      );
    }
    if (path.startsWith("/urban-growth")) {
      return (
        <svg
          viewBox="0 0 24 24"
          className="h-5 w-5"
          aria-hidden="true"
        >
          <circle cx="7" cy="9" r="2" className="fill-current" />
          <path
            d="M4.5 16.5c0-2 1.5-3.5 3.5-3.5s3.5 1.5 3.5 3.5v2H4.5v-2z"
            className="fill-current"
          />
          <path
            d="M13 17v-3.5l3 3 3-5"
            className="stroke-current"
            strokeWidth={1.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </svg>
      );
    }
    if (path.startsWith("/traffic")) {
      return (
        <svg
          viewBox="0 0 24 24"
          className="h-5 w-5"
          aria-hidden="true"
        >
          <path
            d="M7 11l2.2-3.5h5.6L17 11z"
            className="fill-current"
          />
          <rect
            x="5"
            y="11"
            width="14"
            height="5"
            rx="1"
            className="fill-current"
          />
          <circle cx="8.5" cy="17" r="1.3" className="fill-current" />
          <circle cx="15.5" cy="17" r="1.3" className="fill-current" />
        </svg>
      );
    }
    return (
      <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true">
        <circle
          cx="12"
          cy="12"
          r="8"
          className="stroke-current"
          strokeWidth="1.5"
          fill="none"
        />
      </svg>
    );
  };

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-30 flex bg-sidebar text-gray-100 transform transition-transform duration-200 ease-out ${
        isMobileOpen ? "translate-x-0" : "-translate-x-full"
      } md:translate-x-0 ${isCollapsed ? "w-64 md:w-20" : "w-64 md:w-64"}`}
    >
      <div className="relative flex h-full w-full flex-col">
        <div className="px-4 pb-2 pt-6">
          {isCollapsed ? (
            <div className="flex items-center justify-center">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#62d9c5] text-xs font-bold text-sidebar">
                S
              </span>
            </div>
          ) : (
            <div className="text-2xl font-semibold">SUSPS</div>
          )}
        </div>

        {isCollapsed && (
          <div className="mt-3 hidden items-center justify-center md:flex">
            <button
              type="button"
              onClick={onToggleCollapse}
              className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-neutral-100 text-gray-800 shadow-sm hover:bg-neutral-200"
              aria-label="Expand sidebar to search"
            >
              <svg
                viewBox="0 0 24 24"
                className="h-4 w-4"
                aria-hidden="true"
              >
                <circle
                  cx="11"
                  cy="11"
                  r="5.5"
                  className="stroke-current"
                  strokeWidth="1.5"
                  fill="none"
                />
                <line
                  x1="15"
                  y1="15"
                  x2="20"
                  y2="20"
                  className="stroke-current"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
              </svg>
            </button>
          </div>
        )}

        {/* Expanded: full search box (desktop only) */}
        {!isCollapsed && (
          <div
            className="hidden px-4 pb-3 mb-2 md:block"
            onFocus={() => setIsSearchFocused(true)}
            onBlur={(e) => {
              if (!e.currentTarget.contains(e.relatedTarget as Node | null)) {
                setIsSearchFocused(false);
              }
            }}
          >
            <input
              type="text"
              placeholder="Search area..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full rounded-md bg-[#f5f5f5] px-3 py-2 text-sm text-gray-900 placeholder-gray-500 shadow-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-gray-300"
            />
            {isSearchFocused && query.trim().length > 0 && (
              <div className="mt-2 max-h-40 overflow-y-auto text-xs">
                <div className="rounded-md bg-white p-1 shadow-sm">
                  {loading && <p className="text-gray-500">Loading areas...</p>}
                  {error && <p className="text-red-500">{error}</p>}
                  {!loading && !error && suggestions.length === 0 && (
                    <p className="text-gray-500">No results.</p>
                  )}
                  {!loading &&
                    !error &&
                    suggestions.map((area) => (
                      <button
                        key={area.id}
                        type="button"
                        onClick={() => {
                          onSelectArea(area);
                          setQuery("");
                        }}
                        className={`flex w-full items-center justify-between rounded-md px-2 py-1 text-left hover:bg-neutral-100 ${
                          selectedArea && selectedArea.id === area.id
                            ? "bg-neutral-100 font-semibold"
                            : ""
                        }`}
                      >
                        <span className="text-gray-700">{area.name}</span>
                        {area.type && (
                          <span className="text-[10px] uppercase text-gray-400">
                            {area.type}
                          </span>
                        )}
                      </button>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <nav className="mt-4 flex-1 space-y-1 px-2 pb-4">
          {navItems.map((item) => (
            <NavLink key={item.to} to={item.to}>
              {({ isActive }) => (
                <div
                  className={
                    isCollapsed
                      ? `flex justify-center px-0 py-2 text-base transition transform ${
                          isActive
                            ? "text-white"
                            : "text-gray-200 hover:text-white"
                        }`
                      : `block px-3 py-2 text-base transition transform border-l-4 ${
                          isActive
                            ? `bg-[#181818] text-white font-bold scale-105 rounded-none ${item.borderClass}`
                            : "text-gray-200 hover:bg-neutral-700 scale-100 rounded-md border-transparent"
                        }`
                  }
                >
                  <span className="flex items-center gap-2">
                    <span
                      className={
                        isCollapsed
                          ? `flex h-8 w-8 items-center justify-center rounded-full border transition-transform ${
                              isActive
                                ? `${item.iconActiveClass} scale-110`
                                : "border-transparent bg-transparent scale-100"
                            }`
                          : "flex h-6 w-6 items-center justify-center"
                      }
                    >
                      {renderNavIcon(item.to)}
                    </span>
                    {!isCollapsed && <span>{item.label}</span>}
                  </span>
                </div>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Reset / Unload controls */}
        <div className="mt-auto px-4 pb-4 pt-2 border-t border-white/10">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => {
                if (!selectedArea) return;
                onUnloadArea();
              }}
              disabled={!selectedArea}
              className="flex-1 rounded-full border border-red-400 px-2 py-1 text-xs font-medium text-red-300 hover:bg-red-500/10 disabled:cursor-not-allowed disabled:border-red-900 disabled:text-red-800"
            >
              Unload
            </button>
            <button
              type="button"
              onClick={() => {
                if (!selectedArea) return;
                onResetArea();
              }}
              disabled={!selectedArea}
              className="flex-1 rounded-full border border-neutral-300 px-2 py-1 text-xs font-medium text-gray-100 hover:bg-white/10 disabled:cursor-not-allowed disabled:border-neutral-700 disabled:text-neutral-500"
            >
              Reset
            </button>
          </div>
        </div>

        {/* Desktop collapse/expand toggle */}
        <button
          type="button"
          onClick={onToggleCollapse}
          className="absolute -right-3 top-24 hidden h-7 w-7 items-center justify-center rounded-full bg-[#262626] text-gray-100 shadow-sm hover:bg-[#111111] md:flex"
          aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <span className="text-xs font-semibold leading-none">
            {isCollapsed ? ">" : "<"}
          </span>
        </button>
      </div>
    </aside>
  );
}


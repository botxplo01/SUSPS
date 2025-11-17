import { useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import type { Area } from "../types";
import { fetchJson } from "../api";

function titleForPath(pathname: string): string {
  if (pathname.startsWith("/urban-growth")) return "Urban Growth";
  if (pathname.startsWith("/energy")) return "Energy";
  if (pathname.startsWith("/traffic")) return "Traffic";
  return "Dashboard";
}

function gradientForPath(pathname: string, scrolled: boolean): string {
  if (pathname.startsWith("/urban-growth")) {
    return scrolled
      ? "bg-gradient-to-r from-emerald-300 to-lime-200"
      : "bg-gradient-to-r from-emerald-500 to-lime-400";
  }
  if (pathname.startsWith("/energy")) {
    return scrolled
      ? "bg-gradient-to-r from-amber-300 to-orange-200"
      : "bg-gradient-to-r from-amber-500 to-orange-500";
  }
  if (pathname.startsWith("/traffic")) {
    return scrolled
      ? "bg-gradient-to-r from-rose-300 to-red-200"
      : "bg-gradient-to-r from-rose-500 to-red-500";
  }
  return scrolled
    ? "bg-gradient-to-r from-teal-200 to-slate-100"
    : "bg-gradient-to-r from-[#62d9c5] to-[#181818]";
}

function renderHeaderIcon(pathname: string) {
  if (pathname.startsWith("/dashboard")) {
    // Home icon
    return (
      <svg viewBox="0 0 24 24" className="h-7 w-7" aria-hidden="true">
        <path
          d="M3 10.5L12 4l9 6.5V20a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1v-9.5z"
          className="fill-current"
        />
      </svg>
    );
  }
  if (pathname.startsWith("/energy")) {
    // Energy: lightning bolt in a circle
    return (
      <svg viewBox="0 0 24 24" className="h-7 w-7" aria-hidden="true">
        <circle
          cx="12"
          cy="12"
          r="8.5"
          stroke="currentColor"
          strokeWidth="1.5"
          fill="none"
        />
        <path d="M11 5l-3 7h3v7l3-7h-3z" fill="currentColor" />
      </svg>
    );
  }
  if (pathname.startsWith("/urban-growth")) {
    // Urban growth: population + upward trend
    return (
      <svg viewBox="0 0 24 24" className="h-7 w-7" aria-hidden="true">
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
  if (pathname.startsWith("/traffic")) {
    // Traffic: car icon
    return (
      <svg viewBox="0 0 24 24" className="h-7 w-7" aria-hidden="true">
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
  return null;
}

interface HeaderProps {
  onToggleSidebar: () => void;
  selectedArea: Area | null;
  onSelectArea: (area: Area) => void;
  onExportPage?: () => void;
}

export function Header({
  onToggleSidebar,
  selectedArea,
  onSelectArea,
  onExportPage,
}: HeaderProps) {
  const { pathname } = useLocation();
  const title = titleForPath(pathname);
  const [scrolled, setScrolled] = useState(false);
  const gradient = gradientForPath(pathname, scrolled);
  const icon = renderHeaderIcon(pathname);

  const [areas, setAreas] = useState<Area[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [isSearchFocused, setIsSearchFocused] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 4);
    };
    handleScroll();
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    let cancelled = false;
    setSearchLoading(true);
    setSearchError(null);

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
        setSearchError(
          err instanceof Error ? err.message : "Failed to load areas from API.",
        );
      })
      .finally(() => {
        if (!cancelled) setSearchLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const headerBase =
    "sticky top-0 z-20 border-b px-6 shadow-sm backdrop-blur-md transition-colors";
  const headerTone = scrolled
    ? "bg-black/70 border-black/40 text-white"
    : "bg-white border-neutral-200 text-gray-900";
  const iconWrapperClasses = scrolled
    ? "bg-white/10 text-white"
    : "bg-neutral-50 text-gray-900";
  const buttonClasses = scrolled
    ? "border-white/40 text-white bg-white/10 hover:bg-white/20"
    : "border-neutral-300 text-gray-800 hover:bg-neutral-100";
  const mobileMenuButtonClasses = scrolled
    ? "bg-white/20 text-white hover:bg-white/30"
    : "bg-black/5 text-gray-800 hover:bg-black/10";

  const trimmedQuery = searchQuery.trim().toLowerCase();
  const suggestions: Area[] = !trimmedQuery
    ? areas
    : areas
        .map((area) => {
          const name = area.name.toLowerCase();
          const idx = name.indexOf(trimmedQuery);
          if (idx === -1) return null;
          return { area, idx, len: name.length };
        })
        .filter(
          (item): item is { area: Area; idx: number; len: number } => item !== null,
        )
        .sort((a, b) => {
          if (a.idx !== b.idx) return a.idx - b.idx;
          return a.len - b.len;
        })
        .map((s) => s.area);

  return (
    <header className={`${headerBase} ${headerTone} py-4`}>
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <button
            type="button"
            className={`mr-1 inline-flex h-10 w-10 items-center justify-center rounded-full md:hidden ${mobileMenuButtonClasses}`}
            onClick={onToggleSidebar}
            aria-label="Toggle navigation menu"
          >
            <span className="sr-only">Open navigation</span>
            <span className="space-y-1">
              <span className="block h-0.5 w-5 bg-current" />
              <span className="block h-0.5 w-4 bg-current" />
              <span className="block h-0.5 w-6 bg-current" />
            </span>
          </button>
          <div className="flex items-center gap-3">
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-full shadow-sm ${iconWrapperClasses}`}
            >
              {icon}
            </div>
            <h1
              className={`text-2xl font-semibold bg-clip-text text-transparent ${gradient} sm:text-3xl`}
            >
              {title}
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {onExportPage && (
            <button
              type="button"
              onClick={onExportPage}
              className="inline-flex items-center rounded-full bg-blue-900 px-4 py-2 text-xs sm:text-sm font-medium text-white shadow-sm hover:bg-blue-800"
            >
              <svg
                viewBox="0 0 20 20"
                className="mr-1.5 h-4 w-4"
                aria-hidden="true"
              >
                <path
                  d="M10 2a.75.75 0 01.75.75v7.19l2.22-2.22a.75.75 0 111.06 1.06l-3.5 3.5a.75.75 0 01-1.06 0l-3.5-3.5a.75.75 0 111.06-1.06l2.22 2.22V2.75A.75.75 0 0110 2z"
                  className="fill-current"
                />
                <path
                  d="M4 12.75a.75.75 0 011.5 0v1.5h9v-1.5a.75.75 0 011.5 0v2.25A1.25 1.25 0 0114.75 16H5.25A1.25 1.25 0 014 15.25z"
                  className="fill-current"
                />
              </svg>
              Export
            </button>
          )}
          <button
            type="button"
            className={`inline-flex rounded-full px-4 py-2 text-xs sm:text-sm font-medium shadow-sm border ${buttonClasses}`}
          >
            Sign out
          </button>
        </div>
      </div>

      <div
        className="mt-3 md:hidden"
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
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-md bg-[#f5f5f5] px-3 py-2 text-sm text-gray-900 placeholder-gray-500 shadow-sm focus:bg-white focus:outline-none focus:ring-2 focus:ring-gray-300"
        />
        {isSearchFocused && searchQuery.trim().length > 0 && (
          <div className="mt-2 max-h-40 overflow-y-auto text-xs">
            <div className="rounded-md bg-white p-1 shadow-sm">
              {searchLoading && (
                <p className="text-gray-500">Loading areas...</p>
              )}
              {searchError && <p className="text-red-500">{searchError}</p>}
              {!searchLoading && !searchError && suggestions.length === 0 && (
                <p className="text-gray-500">No results.</p>
              )}
              {!searchLoading &&
                !searchError &&
                suggestions.map((area) => (
                  <button
                    key={area.id}
                    type="button"
                    onClick={() => {
                      onSelectArea(area);
                      setSearchQuery("");
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
    </header>
  );
}

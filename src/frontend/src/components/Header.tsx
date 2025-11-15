import { useLocation } from "react-router-dom";

function titleForPath(pathname: string): string {
  if (pathname.startsWith("/urban-growth")) return "Urban Growth";
  if (pathname.startsWith("/energy")) return "Energy";
  if (pathname.startsWith("/traffic")) return "Traffic";
  return "Dashboard";
}

export function Header() {
  const { pathname } = useLocation();
  const title = titleForPath(pathname);

  return (
    <header className="flex items-center justify-between border-b border-neutral-200 bg-white px-6 py-3 shadow-sm">
      <h1 className="text-lg font-semibold text-gray-900">{title}</h1>
      <button
        type="button"
        className="rounded-full border border-neutral-300 px-4 py-1 text-sm font-medium text-gray-800 shadow-sm hover:bg-neutral-100"
      >
        Sign out
      </button>
    </header>
  );
}

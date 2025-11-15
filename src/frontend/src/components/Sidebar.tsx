import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/urban-growth", label: "Urban Growth" },
  { to: "/energy", label: "Energy" },
  { to: "/traffic", label: "Traffic" },
];

export function Sidebar() {
  return (
    <aside className="flex w-64 flex-col bg-sidebar text-gray-100">
      <div className="px-4 pb-4 pt-6 text-2xl font-semibold">SUSPS</div>
      <div className="px-4 pb-4">
        <input
          type="text"
          placeholder="Search area..."
          className="w-full rounded-md bg-neutral-800 px-3 py-2 text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-300"
        />
        <p className="mt-2 text-xs text-gray-300">
          Search suggestions and load area behavior to be implemented.
        </p>
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

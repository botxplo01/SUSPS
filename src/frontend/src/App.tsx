// @author: David Lameck

import { useState, useEffect } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { DashboardPage } from "./pages/Dashboard";
import { UrbanGrowthPage } from "./pages/UrbanGrowth";
import { EnergyPage } from "./pages/Energy";
import { TrafficPage } from "./pages/Traffic";
import { SignInPage } from "./pages/SignIn";
import { SignUpPage } from "./pages/SignUp";
import { RequireAuth } from "./auth/RequireAuth";
import type { Area } from "./types";

/**
 * Root application shell.
 *
 * Wires routing, authentication guard, and the shared selected-area and
 * export-registration state used by the dashboard and domain pages.
 */
export default function App() {
  const [selectedArea, setSelectedArea] = useState<Area | null>(null);
  const [areaResetCounter, setAreaResetCounter] = useState(0);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [pageExporter, setPageExporter] = useState<(() => void) | null>(null);
  const location = useLocation();

  useEffect(() => {
    if (window.location.hostname === "susps-main.onrender.com") {
      console.log("Waking up the backend...");
      fetch("https://susps-web.onrender.com/health")
        .then((res) => {
          if (res.ok) {
            console.log("Backend is awake.");
          } else {
            console.error("Backend wake-up call failed with status:", res.status);
          }
        })
        .catch((err) => {
          console.error("Backend wake-up call failed:", err);
        });
    }
  }, []);


  const isAuthRoute =
    location.pathname === "/signin" || location.pathname === "/signup";

  if (isAuthRoute) {
    return (
      <div className="min-h-screen bg-neutral-900">
        <Routes>
          <Route path="/signin" element={<SignInPage />} />
          <Route path="/signup" element={<SignUpPage />} />
          <Route path="*" element={<Navigate to="/signin" replace />} />
        </Routes>
      </div>
    );
  }

  return (
    <RequireAuth>
      <div className="flex h-screen bg-neutral-100">
        <Sidebar
          selectedArea={selectedArea}
          onSelectArea={(area) => {
            setSelectedArea(area);
            setAreaResetCounter((prev) => prev + 1);
            setIsSidebarOpen(false);
          }}
          onResetArea={() => {
            setAreaResetCounter((prev) => prev + 1);
          }}
          onUnloadArea={() => {
            setSelectedArea(null);
            setAreaResetCounter((prev) => prev + 1);
          }}
          isMobileOpen={isSidebarOpen}
          isCollapsed={isSidebarCollapsed}
          onToggleCollapse={() => setIsSidebarCollapsed((prev) => !prev)}
        />
        {isSidebarOpen && (
          <div
            className="fixed inset-0 z-20 bg-black/40 md:hidden"
            onClick={() => setIsSidebarOpen(false)}
            aria-hidden="true"
          />
        )}
        <div
          className={`flex flex-1 flex-col transition-all ${
            isSidebarCollapsed ? "md:ml-20" : "md:ml-64"
          }`}
        >
          <Header
            onToggleSidebar={() => setIsSidebarOpen((open) => !open)}
            selectedArea={selectedArea}
            onSelectArea={(area) => {
              setSelectedArea(area);
              setIsSidebarOpen(false);
            }}
            onExportPage={pageExporter ? () => pageExporter() : undefined}
          />
          <main className="flex-1 p-4 flex flex-col">
            <div className="flex-1">
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route
                  path="/dashboard"
                  element={
                    <DashboardPage
                      key={`dashboard-${selectedArea?.id ?? "none"}-${areaResetCounter}`}
                      selectedArea={selectedArea}
                      onRegisterExporter={(fn) => setPageExporter(() => fn)}
                    />
                  }
                />
                <Route
                  path="/urban-growth"
                  element={
                    <UrbanGrowthPage
                      key={`growth-${selectedArea?.id ?? "none"}-${areaResetCounter}`}
                      selectedArea={selectedArea}
                      onRegisterExporter={(fn) => setPageExporter(() => fn)}
                    />
                  }
                />
                <Route
                  path="/energy"
                  element={
                    <EnergyPage
                      key={`energy-${selectedArea?.id ?? "none"}-${areaResetCounter}`}
                      selectedArea={selectedArea}
                      onRegisterExporter={(fn) => setPageExporter(() => fn)}
                    />
                  }
                />
                <Route
                  path="/traffic"
                  element={
                    <TrafficPage
                      key={`traffic-${selectedArea?.id ?? "none"}-${areaResetCounter}`}
                      selectedArea={selectedArea}
                      onRegisterExporter={(fn) => setPageExporter(() => fn)}
                    />
                  }
                />
              </Routes>
            </div>
            <Footer />
          </main>
        </div>
      </div>
    </RequireAuth>
  );
}

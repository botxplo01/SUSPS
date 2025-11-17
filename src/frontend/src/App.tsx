import { useState } from "react";
import { Route, Routes, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { Footer } from "./components/Footer";
import { DashboardPage } from "./pages/Dashboard";
import { UrbanGrowthPage } from "./pages/UrbanGrowth";
import { EnergyPage } from "./pages/Energy";
import { TrafficPage } from "./pages/Traffic";
import type { Area } from "./types";

export default function App() {
  const [selectedArea, setSelectedArea] = useState<Area | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [pageExporter, setPageExporter] = useState<(() => void) | null>(null);

  return (
    <div className="flex h-screen bg-neutral-100">
      <Sidebar
        selectedArea={selectedArea}
        onSelectArea={(area) => {
          setSelectedArea(area);
          setIsSidebarOpen(false);
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
                    selectedArea={selectedArea}
                    onRegisterExporter={(fn) => setPageExporter(() => fn)}
                  />
                }
              />
              <Route
                path="/urban-growth"
                element={
                  <UrbanGrowthPage
                    selectedArea={selectedArea}
                    onRegisterExporter={(fn) => setPageExporter(() => fn)}
                  />
                }
              />
              <Route
                path="/energy"
                element={
                  <EnergyPage
                    selectedArea={selectedArea}
                    onRegisterExporter={(fn) => setPageExporter(() => fn)}
                  />
                }
              />
              <Route
                path="/traffic"
                element={
                  <TrafficPage
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
  );
}

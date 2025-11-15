import { useState } from "react";
import { Route, Routes, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { DashboardPage } from "./pages/Dashboard";
import { UrbanGrowthPage } from "./pages/UrbanGrowth";
import { EnergyPage } from "./pages/Energy";
import { TrafficPage } from "./pages/Traffic";
import type { Area } from "./types";

export default function App() {
  const [selectedArea, setSelectedArea] = useState<Area | null>(null);

  return (
    <div className="flex h-screen bg-neutral-100">
      <Sidebar selectedArea={selectedArea} onSelectArea={setSelectedArea} />
      <div className="flex flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-y-auto p-4">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route
              path="/dashboard"
              element={<DashboardPage selectedArea={selectedArea} />}
            />
            <Route
              path="/urban-growth"
              element={<UrbanGrowthPage selectedArea={selectedArea} />}
            />
            <Route
              path="/energy"
              element={<EnergyPage selectedArea={selectedArea} />}
            />
            <Route
              path="/traffic"
              element={<TrafficPage selectedArea={selectedArea} />}
            />
          </Routes>
        </main>
      </div>
    </div>
  );
}

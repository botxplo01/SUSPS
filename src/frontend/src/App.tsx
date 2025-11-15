import { Route, Routes, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";
import { DashboardPage } from "./pages/Dashboard";
import { UrbanGrowthPage } from "./pages/UrbanGrowth";
import { EnergyPage } from "./pages/Energy";
import { TrafficPage } from "./pages/Traffic";

export default function App() {
  return (
    <div className="flex h-screen bg-neutral-100">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-y-auto p-4">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/urban-growth" element={<UrbanGrowthPage />} />
            <Route path="/energy" element={<EnergyPage />} />
            <Route path="/traffic" element={<TrafficPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

import type { ReactNode } from "react";

interface AuthLayoutProps {
  children: ReactNode;
  title: string;
  subtitle: string;
  description: string;
}

export function AuthLayout({ children, title, subtitle, description }: AuthLayoutProps) {
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-white">
      {/* Left: form container (full-height, white background) */}
      <div className="flex flex-1 items-center justify-center bg-white px-6 py-10 md:px-16">
        <div className="w-full max-w-md">
          {children}
        </div>
      </div>

      {/* Right: info container (desktop/tablet, frosted multi-color gradient across full half) */}
      <div className="relative hidden flex-1 items-center justify-center bg-gradient-to-br from-black via-gray-700 via-emerald-500 to-emerald-300 text-white md:flex">
        {/* Frosted glass overlay over the entire right half */}
        <div className="absolute inset-0 bg-white/10 backdrop-blur-xl border-l border-white/10" aria-hidden="true" />
        <div className="relative max-w-md px-10 py-8 text-left">
          <h1 className="text-3xl font-semibold leading-tight md:text-4xl">
            Smart Urban Simulation and Prediction System
          </h1>
          <p className="mt-3 text-sm font-medium text-emerald-200">Developed by David Lameck</p>
          <p className="mt-6 text-sm leading-relaxed text-slate-100">
            SUSPS brings together urban growth, energy, and traffic data to help planners explore scenarios,
            forecast demand, and surface AI-driven insights for more sustainable cities.
          </p>
        </div>
      </div>

      {/* Mobile banner-style info container (frosted multi-color gradient) */}
      <div className="fixed bottom-0 left-0 right-0 z-10 block bg-gradient-to-br from-black via-gray-700 via-emerald-500 to-emerald-300/90 px-6 py-4 text-center text-sm font-medium text-white shadow-2xl backdrop-blur-xl border-t border-white/10 md:hidden">
        <p className="text-base">Smart Urban Simulation and Prediction System</p>
        <p className="mt-1 text-xs text-emerald-100">by David Lameck</p>
      </div>
    </div>
  );
}

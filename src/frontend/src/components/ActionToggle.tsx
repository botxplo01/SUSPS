/** @author: Lameck David Musumpuka **/

import { useState } from "react";
import type { Mode } from "../types";

interface ActionToggleProps {
  mode?: Mode;
  onPredict?: () => void;
  onOptimize?: () => void;
  onSimulate?: () => void;
}

export function ActionToggle({
  mode = "REAL",
  onPredict,
  onOptimize,
  onSimulate,
}: ActionToggleProps) {
  const [selected, setSelected] = useState<
    "predict" | "optimize" | "simulate" | null
  >(null);

  const handlePredict = () => {
    setSelected("predict");
    onPredict?.();
  };

  const handleOptimize = () => {
    setSelected("optimize");
    onOptimize?.();
  };

  const handleSimulate = () => {
    setSelected("simulate");
    onSimulate?.();
  };

  return (
    <div className="fixed bottom-4 right-4 z-20 rounded-full bg-white px-3 py-2 shadow-lg">
      <div className="flex items-center gap-2 text-xs font-medium text-gray-800">
        <button
          type="button"
          onClick={handlePredict}
          className={`rounded-full px-3 py-1 transform transition-all duration-150 ${
            selected === "predict"
              ? "bg-orange-500 text-white shadow-sm hover:bg-orange-600 active:scale-95"
              : "bg-neutral-200 text-gray-800 hover:bg-neutral-300 active:scale-95"
          }`}
        >
          Predict
        </button>
        <button
          type="button"
          onClick={handleOptimize}
          className={`rounded-full px-3 py-1 transform transition-all duration-150 ${
            selected === "optimize"
              ? "bg-emerald-400 text-white shadow-sm hover:bg-emerald-500 active:scale-95"
              : "bg-neutral-200 text-gray-800 hover:bg-neutral-300 active:scale-95"
          }`}
        >
          Optimize
        </button>
        {mode === "SIMULATE" && (
          <button
            type="button"
            onClick={handleSimulate}
            className={`rounded-full px-3 py-1 transform transition-all duration-150 ${
              selected === "simulate"
                ? "bg-sky-500 text-white shadow-sm hover:bg-sky-600 active:scale-95"
                : "bg-neutral-200 text-gray-800 hover:bg-neutral-300 active:scale-95"
            }`}
          >
            Simulate
          </button>
        )}
      </div>
    </div>
  );
}


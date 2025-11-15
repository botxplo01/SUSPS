import type { Mode } from "../types";

interface ActionToggleProps {
  mode?: Mode;
  onPredict?: () => void;
  onOptimize?: () => void;
  onSimulate?: () => void;
}

export function ActionToggle({ mode = "REAL", onPredict, onOptimize, onSimulate }: ActionToggleProps) {
  const isReal = mode === "REAL";
  const isSimulate = mode === "SIMULATE";

  return (
    <div className="fixed bottom-4 right-4 z-20 rounded-full bg-white px-3 py-2 shadow-lg">
      <div className="flex items-center gap-2 text-xs font-medium text-gray-800">
        <button
          type="button"
          onClick={onPredict}
          className={`rounded-full px-3 py-1 transition-colors ${
            isReal
              ? "bg-orange-500 text-white shadow-sm"
              : "bg-neutral-200 text-gray-800 hover:bg-neutral-300"
          }`}
        >
          Predict
        </button>
        <button
          type="button"
          onClick={onOptimize}
          className={`rounded-full px-3 py-1 transition-colors ${
            !isReal && !isSimulate
              ? "bg-emerald-400 text-white shadow-sm"
              : "bg-neutral-200 text-gray-800 hover:bg-neutral-300"
          }`}
        >
          Optimize
        </button>
        <button
          type="button"
          onClick={onSimulate}
          className={`rounded-full px-3 py-1 transition-colors ${
            isSimulate
              ? "bg-sky-500 text-white shadow-sm"
              : "bg-neutral-200 text-gray-800 hover:bg-neutral-300"
          }`}
        >
          Simulate
        </button>
      </div>
    </div>
  );
}

interface ActionToggleProps {
  onPredict?: () => void;
  onOptimize?: () => void;
  onSimulate?: () => void;
}

export function ActionToggle({ onPredict, onOptimize, onSimulate }: ActionToggleProps) {
  return (
    <div className="fixed bottom-4 left-4 z-20 rounded-full bg-white px-3 py-2 shadow-lg">
      <div className="flex items-center gap-2 text-xs font-medium text-gray-800">
        <button
          type="button"
          onClick={onPredict}
          className="rounded-full bg-neutral-900 px-3 py-1 text-white hover:bg-black"
        >
          Predict
        </button>
        <button
          type="button"
          onClick={onOptimize}
          className="rounded-full bg-neutral-200 px-3 py-1 hover:bg-neutral-300"
        >
          Optimize
        </button>
        <button
          type="button"
          onClick={onSimulate}
          className="rounded-full bg-neutral-200 px-3 py-1 hover:bg-neutral-300"
        >
          Simulate
        </button>
      </div>
    </div>
  );
}

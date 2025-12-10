/** @author: David Lameck **/

type Mode = "REAL" | "SIMULATE";

interface ModeToggleProps {
  mode: Mode;
  onChange?: (mode: Mode) => void;
}

export function ModeToggle({ mode, onChange }: ModeToggleProps) {
  const isReal = mode === "REAL";

  return (
    <div className="inline-flex rounded-full bg-neutral-200 p-1 text-xs font-medium">
      <button
        type="button"
        onClick={() => onChange?.("REAL")}
        className={`rounded-full px-3 py-1 transition ${
          isReal ? "bg-black text-white" : "text-gray-700"
        }`}
      >
        Real
      </button>
      <button
        type="button"
        onClick={() => onChange?.("SIMULATE")}
        className={`rounded-full px-3 py-1 transition ${
          !isReal ? "bg-[#1d4ed8] text-white" : "text-gray-700"
        }`}
      >
        Simulate
      </button>
    </div>
  );
}

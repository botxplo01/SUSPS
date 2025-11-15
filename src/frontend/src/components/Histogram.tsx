interface HistogramProps {
  title?: string;
}

export function Histogram({ title }: HistogramProps) {
  return (
    <section className="rounded-xl bg-white p-4 shadow-sm">
      {title && <h2 className="mb-2 text-sm font-semibold text-gray-800">{title}</h2>}
      <div className="flex h-40 items-center justify-center text-xs text-gray-500">
        Histogram visualization to be implemented (no gridlines).
      </div>
    </section>
  );
}

interface InsightsSectionProps {
  children?: React.ReactNode;
}

export function InsightsSection({ children }: InsightsSectionProps) {
  return (
    <section className="rounded-xl bg-white p-4 shadow-sm">
      <h2 className="mb-2 text-sm font-semibold text-gray-800">Insights</h2>
      <div className="text-sm text-gray-700">
        {children ?? "Model-driven insights will be rendered here."}
      </div>
    </section>
  );
}

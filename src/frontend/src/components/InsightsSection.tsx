interface InsightsSectionProps {
  children?: React.ReactNode;
}

export function InsightsSection({ children }: InsightsSectionProps) {
  return (
    <section className="relative overflow-hidden rounded-xl bg-gradient-to-br from-emerald-400/30 via-sky-400/30 to-indigo-500/30 p-[1px] shadow-sm">
      <div className="relative rounded-[0.75rem] bg-white/70 backdrop-blur-md p-4">
        <h2 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-900">
          <span className="inline-flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-500 to-fuchsia-500 text-white shadow-sm">
            <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true">
              <circle cx="12" cy="12" r="5.5" className="stroke-current" strokeWidth="1.4" fill="none" />
              <path
                d="M7 12c1.4-.8 2.7-1.2 5-1.2 2.2 0 3.6.4 5 1.2"
                className="stroke-current"
                strokeWidth="1.3"
                strokeLinecap="round"
                fill="none"
              />
              <circle cx="9" cy="10.2" r="0.9" className="fill-current" />
              <circle cx="14.5" cy="13.2" r="0.7" className="fill-current" />
            </svg>
          </span>
          <span>Insights</span>
        </h2>
        <div className="text-sm text-gray-800">
          {children ?? "Model-driven insights will be rendered here."}
        </div>
      </div>
    </section>
  );
}

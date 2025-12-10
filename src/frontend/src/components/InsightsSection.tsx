/** @author: Lameck David Musumpuka **/

interface InsightsSectionProps {
  children?: React.ReactNode;
}

export function InsightsSection({ children }: InsightsSectionProps) {
  return (
    <section className="relative rounded-xl bg-gradient-to-br from-emerald-400/30 via-sky-400/30 to-indigo-500/30 p-[1px] shadow-sm">
      <div className="relative rounded-[0.75rem] bg-white/70 backdrop-blur-md p-4">
        <h2 className="mb-3 flex items-center gap-2 text-base font-semibold text-gray-900 md:text-lg">
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-500 to-fuchsia-500 text-white shadow-sm">
            <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden="true">
              {/* Sparkle-style four-point icon, inspired by the attached image */}
              <path
                d="M12 3.5 14.1 9.1 20 11 14.1 12.9 12 18.5 9.9 12.9 4 11 9.9 9.1 12 3.5z"
                fill="white"
              />
            </svg>
          </span>
          <span>AI Analysis &amp; Insights</span>
        </h2>
        <div className="text-sm leading-relaxed text-gray-800">
          {children ?? "Model-driven insights will be rendered here."}
        </div>
      </div>
    </section>
  );
}

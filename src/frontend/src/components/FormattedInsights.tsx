interface FormattedInsightsProps {
  text: string;
}

// Render advisory/insights text in a normal, non-markdown style while
// preserving key headings as bold.
export function FormattedInsights({ text }: FormattedInsightsProps) {
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  const elements: JSX.Element[] = [];

  for (const raw of lines) {
    let line = raw.trim();
    if (!line) continue;

    const lower = line.toLowerCase();

    // Drop duplicate/markdown headings like "Insights" or "### Insights".
    if (lower === "insights" || lower.startsWith("### insights")) {
      continue;
    }

    // Skip markdown underline lines (e.g. "=====").
    if (/^=+$/.test(line)) {
      continue;
    }

    // Strip common markdown markers.
    line = line.replace(/^#{1,6}\s*/, ""); // leading #
    line = line.replace(/^\*\s+/, ""); // leading bullet *
    line = line.replace(/^\d+\.\s+/, ""); // numbered list
    line = line.replace(/\*\*/g, ""); // bold markers

    if (!line) continue;

    // Main title, e.g. "Urban Analytics Insights for Nairobi".
    if (/^Urban Analytics Insights for /i.test(line)) {
      elements.push(
        <p key={elements.length} className="font-semibold">
          {line}
        </p>,
      );
      continue;
    }

    // Section heading: "Recommended Actions".
    if (/^Recommended Actions/i.test(line)) {
      elements.push(
        <p key={elements.length} className="mt-2 font-semibold">
          {line}
        </p>,
      );
      continue;
    }

    // Sub-headings: Short-term / Medium-term / Long-term.
    if (/^Short-term\b/i.test(line)) {
      const base = "Short-term";
      const suffix = line.slice(base.length);
      elements.push(
        <p key={elements.length} className="mt-1">
          <span className="font-semibold">{base}</span>
          {suffix}
        </p>,
      );
      continue;
    }

    if (/^Medium-term\b/i.test(line)) {
      const base = "Medium-term";
      const suffix = line.slice(base.length);
      elements.push(
        <p key={elements.length} className="mt-1">
          <span className="font-semibold">{base}</span>
          {suffix}
        </p>,
      );
      continue;
    }

    if (/^Long-term\b/i.test(line)) {
      const base = "Long-term";
      const suffix = line.slice(base.length);
      elements.push(
        <p key={elements.length} className="mt-1">
          <span className="font-semibold">{base}</span>
          {suffix}
        </p>,
      );
      continue;
    }

    // Everything else: plain paragraph text.
    elements.push(
      <p key={elements.length}>{line}</p>,
    );
  }

  return <div className="space-y-1 leading-relaxed">{elements}</div>;
}

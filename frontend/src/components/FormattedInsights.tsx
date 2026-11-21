/** @author: David Lameck **/

interface FormattedInsightsProps {
  text: string;
}

// Render advisory/insights text in a normal, non-markdown style while
// preserving key headings as bold.
export function FormattedInsights({ text }: FormattedInsightsProps) {

  // Normalise newlines and gently split markdown-style headings and numbered
  // items so that the layout is closer to the PDF/export formatting.
  let normalised = text.replace(/\r\n/g, "\n");

  // Ensure markdown headings like "### Energy Profile" start on their own line.
  normalised = normalised.replace(/\s*###\s+/g, "\n### ");

  // Ensure a leading "**Insights**" marker is on its own line so we can drop it.
  normalised = normalised.replace(/\s*\*\*\s*Insights\s*\*\*/gi, "\nInsights\n");
  
  // Insert line breaks before simple numbered items like "1. text" when they
  // appear inline with other content.
  normalised = normalised.replace(/(\S)\s+(\d+\.\s)/g, "$1\n$2");

  const lines = normalised.split("\n");
  const elements: JSX.Element[] = [];
  let pendingOrdered: string[] = [];
  let pendingBullets: string[] = [];

  const flushOrdered = () => {
    if (!pendingOrdered.length) return;
    elements.push(
      <ol
        key={`olist-${elements.length}`}
        className="ml-4 list-decimal space-y-1 text-[13px] text-gray-800"
      >
        {pendingOrdered.map((item, idx) => (
          <li key={idx}>{item}</li>
        ))}
      </ol>,
    );
    pendingOrdered = [];
  };

  const flushBullets = () => {
    if (!pendingBullets.length) return;
    elements.push(
      <ul
        key={`ulist-${elements.length}`}
        className="ml-4 list-disc space-y-1 text-[13px] text-gray-800"
      >
        {pendingBullets.map((item, idx) => (
          <li key={idx}>{item}</li>
        ))}
      </ul>,
    );
    pendingBullets = [];
  };

  for (const raw of lines) {
    let line = raw.trim();
    if (!line) continue;

    const lowerRaw = line.toLowerCase();

    // Skip lines marked for removal.
    if (/\(remove this\)/i.test(lowerRaw)) {
      continue;
    }

    // Drop markdown bold markers.
    line = line.replace(/\(bold\)/gi, "").trim();
    if (!line) continue;

    const lower = line.toLowerCase();

    // Drop duplicate/markdown headings like "Insights" or "### Insights".
    if (lower === "insights" || lower.startsWith("### insights")) {
      continue;
    }

    // Skip markdown underline lines (e.g. "=====", "-----").
    if (/^=+$/.test(line) || /^[-_]+$/.test(line)) {
      continue;
    }

    // Detect simple numbered list items like "1. text", "2. text" and collect
    // them into an ordered list that will be flushed when the sequence ends.
    const orderedMatch = line.match(/^(\d+)\.\s+(.*)$/);
    if (orderedMatch) {
      const itemRaw = orderedMatch[2].trim();
      const item = itemRaw.replace(/\*\*/g, "").replace(/\(bold\)/gi, "").trim();
      if (item) {
        pendingOrdered.push(item);
      }
      continue;
    }

    // Detect simple unordered bullet items like "- text" or "* text".
    const bulletMatch = line.match(/^[-*]\s+(.*)$/);
    if (bulletMatch) {
      const itemRaw = bulletMatch[1].trim();
      const item = itemRaw.replace(/\*\*/g, "").replace(/\(bold\)/gi, "").trim();
      if (item) {
        pendingBullets.push(item);
      }
      continue;
    }

    // Non-list content: flush any pending lists before rendering headings or
    // paragraphs.
    flushOrdered();
    flushBullets();

    // Strip common markdown markers (except list markers, handled above).
    line = line.replace(/^#{1,6}\s*/, ""); // leading #
    line = line.replace(/\*\*/g, ""); // bold markers

    if (!line) continue;

    // Main title, e.g. "Urban Analytics Insights for Nairobi".
    if (/^Urban Analytics Insights for /i.test(line)) {
      elements.push(
        <p
          key={elements.length}
          className="text-sm font-semibold text-gray-900 md:text-[0.95rem]"
        >
          {line}
        </p>,
      );
      continue;
    }

    // Section heading: "Recommended Actions".
    if (/^Recommended Actions/i.test(line)) {
      elements.push(
        <p key={elements.length} className="mt-3 text-sm font-semibold text-gray-900">
          {line}
        </p>,
      );
      continue;
    }

    // Profile-style headings like "Energy Profile", "Traffic Profile",
    // or "Growth in Population" should render as bold section titles.
    const isProfileHeading =
      ((/profile\b/i.test(line) && !/[.!?]/.test(line)) ||
        /growth in population/i.test(line)) &&
      line.length <= 60;

    // Named headings that appear in advisory output and should be emphasized,
    // even when they do not contain the word "profile".
    const isNamedHeading =
      /^(population growth|traffic enrichment|traffic enriched|urban hotspots?)/i.test(
        line,
      ) && line.length <= 80;

    if (isProfileHeading || isNamedHeading) {
      elements.push(
        <p key={elements.length} className="mt-2 text-[13px] font-semibold text-gray-900">
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
        <p key={elements.length} className="mt-1 text-[13px] text-gray-900">
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
        <p key={elements.length} className="mt-1 text-[13px] text-gray-900">
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
        <p key={elements.length} className="mt-1 text-[13px] text-gray-900">
          <span className="font-semibold">{base}</span>
          {suffix}
        </p>,
      );
      continue;
    }

    // Everything else: plain paragraph text.
    elements.push(
      <p key={elements.length} className="text-[13px] text-gray-800">
        {line}
      </p>,
    );
  }

  // Flush any trailing list items.
  flushOrdered();
  flushBullets();

  return <div className="space-y-1.5 leading-relaxed">{elements}</div>;
}


interface DescriptionSectionProps {
  title: string;
  children?: React.ReactNode;
}

export function DescriptionSection({ title, children }: DescriptionSectionProps) {
  return (
    <section className="rounded-xl bg-white p-4 shadow-sm">
      <h2 className="mb-2 text-sm font-semibold text-gray-800">{title}</h2>
      <div className="text-sm text-gray-700">
        {children ?? "Description content to be implemented."}
      </div>
    </section>
  );
}

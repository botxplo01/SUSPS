/** @author: Lameck David Musumpuka **/

interface AreaBadgeProps {
  name: string;
}

export function AreaBadge({ name }: AreaBadgeProps) {
  const isSelected = name !== "No area selected";
  const baseClasses =
    "inline-flex items-center rounded-full px-3 py-1 text-xs font-medium";
  const colorClasses = isSelected
    ? "bg-[#d2f3e6] text-gray-800"
    : "bg-neutral-200 text-gray-800";

  return <span className={`${baseClasses} ${colorClasses}`}>Area: {name}</span>;
}


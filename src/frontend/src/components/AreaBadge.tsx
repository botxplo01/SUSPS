interface AreaBadgeProps {
  name: string;
}

export function AreaBadge({ name }: AreaBadgeProps) {
  return (
    <span className="inline-flex items-center rounded-full bg-neutral-200 px-3 py-1 text-xs font-medium text-gray-800">
      Area: {name}
    </span>
  );
}

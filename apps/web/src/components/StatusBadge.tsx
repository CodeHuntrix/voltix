import {
  severityBadgeClass,
  stateBadgeClass,
} from "@/lib/machineArt";

type Props = {
  state?: string;
  severity?: string;
  children?: React.ReactNode;
  className?: string;
};

export function StatusBadge({ state, severity, children, className = "" }: Props) {
  const tone =
    severity != null && severity !== ""
      ? severityBadgeClass(severity)
      : stateBadgeClass(state ?? "OFF");
  return (
    <span
      className={`rounded-md px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${tone} ${className}`}
    >
      {children ?? severity ?? state}
    </span>
  );
}

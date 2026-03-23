"use client";

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  icon?: React.ReactNode;
  trend?: "up" | "down" | "flat";
}

export function MetricCard({ label, value, unit, icon, trend }: MetricCardProps) {
  const trendColor =
    trend === "up" ? "text-stressed" : trend === "down" ? "text-neutral" : "text-muted";
  const trendArrow = trend === "up" ? "↑" : trend === "down" ? "↓" : "→";

  return (
    <div className="rounded-xl border border-border bg-surface p-4 flex flex-col gap-1">
      <div className="flex items-center gap-2">
        {icon && <span className="text-muted">{icon}</span>}
        <span className="text-xs text-muted uppercase tracking-wide">{label}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-white">{value}</span>
        {unit && <span className="text-sm text-muted">{unit}</span>}
        {trend && (
          <span className={`text-sm ml-2 ${trendColor}`}>{trendArrow}</span>
        )}
      </div>
    </div>
  );
}

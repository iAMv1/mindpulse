"use client";

interface RiskMeterProps {
  score: number;
  size?: "sm" | "md" | "lg";
}

export function RiskMeter({ score, size = "lg" }: RiskMeterProps) {
  const color =
    score < 40 ? "#2ecc71" : score < 70 ? "#f39c12" : "#e74c3c";
  const label =
    score < 40 ? "NEUTRAL" : score < 70 ? "MILD" : "STRESSED";
  const dims = { sm: 120, md: 180, lg: 260 }[size];
  const strokeWidth = size === "lg" ? 14 : 10;
  const radius = (dims - strokeWidth) / 2;
  const circumference = Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center gap-2">
      <svg width={dims} height={dims / 2 + 20} viewBox={`0 0 ${dims} ${dims / 2 + 20}`}>
        {/* Background arc */}
        <path
          d={describeArc(dims / 2, dims / 2, radius, 180, 360)}
          fill="none"
          stroke="#3A3A4A"
          strokeWidth={strokeWidth}
          strokeLinecap="round"
        />
        {/* Value arc */}
        <path
          d={describeArc(dims / 2, dims / 2, radius, 180, 360)}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={`${circumference}`}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease, stroke 0.5s ease" }}
        />
        {/* Score text */}
        <text
          x={dims / 2}
          y={dims / 2 - 10}
          textAnchor="middle"
          fill={color}
          fontSize={size === "lg" ? 42 : 28}
          fontWeight={800}
          fontFamily="monospace"
        >
          {Math.round(score)}
        </text>
        <text
          x={dims / 2}
          y={dims / 2 + 18}
          textAnchor="middle"
          fill="#a0a0b0"
          fontSize={size === "lg" ? 14 : 11}
        >
          / 100
        </text>
      </svg>
      <span
        className="font-bold text-lg tracking-wider"
        style={{ color }}
      >
        {label}
      </span>
    </div>
  );
}

function describeArc(
  cx: number,
  cy: number,
  r: number,
  startAngle: number,
  endAngle: number
): string {
  const start = polarToCartesian(cx, cy, r, endAngle);
  const end = polarToCartesian(cx, cy, r, startAngle);
  const largeArc = endAngle - startAngle <= 180 ? 0 : 1;
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 0 ${end.x} ${end.y}`;
}

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

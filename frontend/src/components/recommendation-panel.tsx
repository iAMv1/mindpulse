"use client";

interface RecommendationPanelProps {
  score: number;
  level: string;
}

export function RecommendationPanel({ score, level }: RecommendationPanelProps) {
  if (score < 40) {
    return (
      <div className="rounded-xl border border-neutral/30 bg-neutral/5 p-4">
        <h3 className="text-neutral font-semibold mb-2">Calm / Focused</h3>
        <ul className="text-sm text-muted space-y-1">
          <li>Continue current pace</li>
          <li>Take a preventive 2-min eye break every 30-40 min</li>
        </ul>
      </div>
    );
  }
  if (score < 70) {
    return (
      <div className="rounded-xl border border-mild/30 bg-mild/5 p-4">
        <h3 className="text-mild font-semibold mb-2">Mild Stress Detected</h3>
        <ul className="text-sm text-muted space-y-1">
          <li>Do 2 minutes of slow breathing</li>
          <li>Hydrate</li>
          <li>Reset posture + neck stretch</li>
        </ul>
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-stressed/30 bg-stressed/5 p-4">
      <h3 className="text-stressed font-semibold mb-2">Elevated Stress</h3>
      <ol className="text-sm text-muted space-y-1 list-decimal list-inside">
        <li>4 cycles of box breathing</li>
        <li>5-minute screen break</li>
        <li>Resume with one priority task only</li>
      </ol>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { Activity, TrendingUp, Heart, Sparkles } from "lucide-react";
import { api } from "@/lib/api";
import type { InterventionEvent, InterventionSnapshot } from "@/lib/types";

const STATE_LABELS: Record<string, string> = {
  NORMAL: "Stable",
  EARLY_WARNING: "Dipping",
  BREAK_RECOMMENDED: "Low energy",
  RECOVERY: "Recovering",
};

const TREND_LABELS: Record<string, string> = {
  rising: "warming",
  steady: "steady",
  falling: "cooling",
};

const STATE_COLORS: Record<string, string> = {
  NORMAL: "#22c55e",
  EARLY_WARNING: "#d97706",
  BREAK_RECOMMENDED: "#dc2626",
  RECOVERY: "#5b4fc4",
};

const ACTION_EMOJI: Record<string, string> = {
  helped: "✨",
  not_helped: "😐",
  snoozed: "⏰",
  skipped: "→",
  start_break: "🧘",
};

export default function InterventionsPage() {
  const [snapshot, setSnapshot] = useState<InterventionSnapshot | null>(null);
  const [events, setEvents] = useState<InterventionEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.interventionRecommendation("demo_user").catch(() => null),
      api.interventionHistory("demo_user", 168).catch(() => []),
    ]).then(([s, e]) => {
      setSnapshot(s);
      setEvents(e);
      setLoading(false);
    });
  }, []);

  const calculateMeanRecovery = (allEvents: InterventionEvent[]) => {
    const helpedEvents = allEvents.filter((e) => e.action === "helped");
    if (helpedEvents.length === 0) return "0.0";
    const avg = helpedEvents.reduce((acc, e) => acc + (e.recovery_score || 0), 0) / helpedEvents.length;
    return avg.toFixed(1);
  };
  const meanRecovery = calculateMeanRecovery(events);

  const alertState = snapshot?.alert_state ?? "NORMAL";
  const trend = snapshot?.trend ?? "steady";
  const stateColor = STATE_COLORS[alertState] ?? "#22c55e";

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto" style={{ background: "#0a0a0f", minHeight: "100vh" }}>
      <div>
        <h1 className="text-3xl font-semibold tracking-tight" style={{ color: "#F2EFE9" }}>Guidance</h1>
        <p className="text-sm mt-1.5" style={{ color: "#857F75" }}>Gentle suggestions, not commands</p>
      </div>

      <div className="rounded-lg p-6" style={{ background: "#141420", border: "1px solid #1c1c2e" }}>
        <h3 className="text-lg font-medium mb-4" style={{ color: "#F2EFE9" }}>Your current state</h3>
        {loading ? (
          <div className="h-20 flex items-center justify-center">
            <div className="text-sm animate-pulse" style={{ color: "#857F75" }}>Reading your rhythm...</div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-lg" style={{ background: "#1c1c2e" }}>
              <div className="flex items-center gap-2 mb-2">
                <Activity size={16} style={{ color: stateColor }} />
                <div className="text-xs font-medium" style={{ color: "#857F75" }}>Rhythm state</div>
              </div>
              <div className="text-lg font-semibold tabular-nums" style={{ color: stateColor }}>
                {STATE_LABELS[alertState] ?? alertState}
              </div>
            </div>
            <div className="p-4 rounded-lg" style={{ background: "#1c1c2e" }}>
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp size={16} style={{ color: "#5b4fc4" }} />
                <div className="text-xs font-medium" style={{ color: "#857F75" }}>Trend</div>
              </div>
              <div className="text-lg font-semibold tabular-nums" style={{ color: "#F2EFE9" }}>
                {TREND_LABELS[trend] ?? trend}
              </div>
            </div>
            <div className="p-4 rounded-lg" style={{ background: "#1c1c2e" }}>
              <div className="flex items-center gap-2 mb-2">
                <Heart size={16} style={{ color: "#22c55e" }} />
                <div className="text-xs font-medium" style={{ color: "#857F75" }}>Breaks that helped</div>
              </div>
              <div className="text-lg font-semibold tabular-nums" style={{ color: "#22c55e" }}>
                +{meanRecovery}
              </div>
            </div>
          </div>
        )}
      </div>

      {snapshot?.intervention && (
        <div
          className="rounded-lg p-6"
          style={{
            background: "#141420",
            border: "1px solid #1c1c2e",
            borderLeft: `4px solid #5b4fc4`,
          }}
        >
          <h3 className="text-lg font-medium mb-3 flex items-center gap-2" style={{ color: "#F2EFE9" }}>
            <Sparkles size={18} style={{ color: "#5b4fc4" }} />
            Suggested for you: {snapshot.intervention.title}
          </h3>
          <p className="text-sm mb-4" style={{ color: "#857F75" }}>{snapshot.intervention.expected_benefit}</p>
          <ol className="space-y-1.5 text-sm list-none" style={{ color: "#857F75" }}>
            {snapshot.intervention.steps.map((step, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-medium" style={{ background: "#1c1c2e", color: "#5b4fc4" }}>
                  {i + 1}
                </span>
                <span>{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      <div className="rounded-lg p-6" style={{ background: "#141420", border: "1px solid #1c1c2e" }}>
        <h3 className="text-lg font-medium mb-4" style={{ color: "#F2EFE9" }}>Break history</h3>
        <div className="space-y-3 max-h-96 overflow-auto">
          {events.length === 0 && !loading && (
            <p className="text-sm py-4" style={{ color: "#857F75" }}>No breaks yet — your rhythm has been steady! 🎯</p>
          )}
          {events.map((event, i) => {
            const emoji = ACTION_EMOJI[event.action] ?? "";
            const recoveryPositive = (event.recovery_score ?? 0) > 0;
            const recoveryColor = recoveryPositive ? "#22c55e" : "#857F75";

            return (
              <div
                key={i}
                className="rounded-lg p-4 grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm"
                style={{ background: "#1c1c2e" }}
              >
                <div>
                  <div className="text-xs font-medium" style={{ color: "#857F75" }}>When</div>
                  <div className="tabular-nums" style={{ color: "#F2EFE9" }}>
                    {new Date(event.timestamp * 1000).toLocaleString()}
                  </div>
                </div>
                <div>
                  <div className="text-xs font-medium" style={{ color: "#857F75" }}>Action</div>
                  <div style={{ color: "#F2EFE9" }}>
                    {emoji} {event.action}
                  </div>
                  <div style={{ color: "#857F75" }}>{event.intervention_type}</div>
                </div>
                <div>
                  <div className="text-xs font-medium" style={{ color: "#857F75" }}>Score</div>
                  <div className="tabular-nums" style={{ color: "#F2EFE9" }}>
                    {event.score_before.toFixed(1)} → {event.score_after.toFixed(1)}
                  </div>
                  <div className="tabular-nums font-medium" style={{ color: recoveryColor }}>
                    {event.recovery_score ? `+${event.recovery_score.toFixed(1)}` : "--"}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

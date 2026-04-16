"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { InterventionSnapshot } from "@/lib/types";

// ─── Confusion Matrix Component ───
function ConfusionMatrix({ matrix, labels }: { matrix: number[][]; labels: string[] }) {
  const maxVal = Math.max(...matrix.flat(), 1);
  const colors = ["#22c55e", "#d97706", "#dc2626"];

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="p-2 text-xs text-muted"></th>
            <th colSpan={3} className="p-2 text-xs text-muted text-center font-medium">Predicted</th>
          </tr>
          <tr>
            <th className="p-2 text-xs text-muted"></th>
            {labels.map((l, i) => (
              <th key={i} className="p-2 text-xs font-semibold text-center" style={{ color: colors[i] }}>
                {l}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, ri) => (
            <tr key={ri}>
              <td className="p-2 text-xs font-semibold text-right pr-3" style={{ color: colors[ri] }}>
                {ri === 0 && <span className="text-muted text-[10px] block">Actual</span>}
                {labels[ri]}
              </td>
              {row.map((val, ci) => {
                const intensity = val / maxVal;
                const isDiag = ri === ci;
                return (
                  <td
                    key={ci}
                    className="p-3 text-center text-lg font-bold rounded-md border border-border/30 tabular-nums"
                    style={{
                      backgroundColor: isDiag
                        ? `rgba(34, 197, 94, ${0.1 + intensity * 0.3})`
                        : val > 0
                        ? `rgba(220, 38, 38, ${0.05 + intensity * 0.2})`
                        : "rgba(255,255,255,0.02)",
                      color: isDiag ? "#22c55e" : val > 0 ? "#dc2626" : "#4a4a5a",
                    }}
                  >
                    {val}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ─── Metric Card ───
function MetricCard({ label, value, unit, color }: { label: string; value: number; unit: string; color: string }) {
  return (
    <div className="p-4 rounded-lg bg-surface-hover text-center">
      <div className="text-xs text-muted mb-1.5 font-medium">{label}</div>
      <div className="text-3xl font-semibold tabular-nums" style={{ color }}>
        {value}
        <span className="text-sm font-normal text-muted">{unit}</span>
      </div>
    </div>
  );
}

// ─── Main Insights Page ───
export default function InsightsPage() {
  const [metrics, setMetrics] = useState<{
    accuracy: number;
    precision: number;
    recall: number;
    f1: number;
    confusion_matrix: number[][];
    labels: string[];
  } | null>(null);
  const [interventionSnapshot, setInterventionSnapshot] = useState<InterventionSnapshot | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.modelMetrics().catch(() => null),
      api.interventionRecommendation("demo_user").catch(() => null),
    ]).then(([m, s]) => {
      setMetrics(m);
      setInterventionSnapshot(s);
      setLoading(false);
    });
  }, []);

  return (
    <div className="p-8 space-y-8 max-w-6xl mx-auto">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight text-white">Insights</h1>
        <p className="text-sm text-muted mt-1.5">Understand what drives your stress scores</p>
      </div>

      {/* Model Performance Metrics */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <h3 className="text-lg font-medium mb-5 text-white">Model performance</h3>
        {loading ? (
          <div className="h-40 flex items-center justify-center">
            <div className="text-sm text-muted animate-pulse">Loading metrics...</div>
          </div>
        ) : metrics ? (
          <>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <MetricCard label="Accuracy" value={metrics.accuracy} unit="%" color="#22c55e" />
              <MetricCard label="Precision (macro)" value={metrics.precision} unit="%" color="#3b82f6" />
              <MetricCard label="Recall (macro)" value={metrics.recall} unit="%" color="#d97706" />
              <MetricCard label="F1 Score (macro)" value={metrics.f1} unit="%" color="#a78bfa" />
            </div>
            <h4 className="text-sm font-medium mb-3 text-muted">Confusion matrix</h4>
            <ConfusionMatrix matrix={metrics.confusion_matrix} labels={metrics.labels} />
            <p className="text-xs text-muted mt-4">
              Evaluated on 600 synthetic samples generated from the same distribution as training data.
              Diagonal cells (green) = correct predictions. Off-diagonal cells (red) = misclassifications.
            </p>
          </>
        ) : (
          <p className="text-sm text-muted">Failed to load model metrics.</p>
        )}
      </div>

      {/* Feature Importance */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <h3 className="text-lg font-medium mb-5 text-white">Top stress indicators</h3>
        <div className="space-y-3">
          {[
            { name: "Session fragmentation", pct: 35.6, desc: "How scattered your work sessions are" },
            { name: "Rage click count", pct: 27.6, desc: "Rapid frustrated clicking detected" },
            { name: "Switch entropy", pct: 12.7, desc: "Randomness of app/tab switching" },
            { name: "Mouse speed std", pct: 4.6, desc: "Inconsistency of mouse movements" },
            { name: "Scroll velocity std", pct: 4.2, desc: "Erratic scrolling patterns" },
            { name: "Direction change rate", pct: 3.7, desc: "Cursor indecision or hesitation" },
            { name: "Rhythm entropy", pct: 3.7, desc: "Chaos in typing rhythm" },
          ].map((f, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-44 text-sm text-white font-medium">{f.name}</div>
              <div className="flex-1 h-3 bg-surface-hover rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent/80 rounded-full transition-all duration-500"
                  style={{ width: `${f.pct * 100 / 35.6}%` }}
                />
              </div>
              <div className="w-12 text-right text-sm text-muted tabular-nums">{f.pct}%</div>
              <div className="w-60 text-xs text-muted">{f.desc}</div>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted mt-5">
          Our 3 novel features (session fragmentation, rage clicks, switch entropy) account for 75.9% of model decisions.
          Traditional keystroke features (hold/flight times) contribute only ~2%.
        </p>
      </div>

      {/* Research Context */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <h3 className="text-lg font-medium mb-5 text-white">Research benchmarks</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-surface-hover">
            <div className="text-sm text-muted font-medium">Universal model (no calibration)</div>
            <div className="text-2xl font-semibold tabular-nums text-mild mt-2">F1: 0.25 – 0.40</div>
            <div className="text-xs text-muted mt-1.5">Naegelin et al. 2025, 36 employees, 8-week field study</div>
          </div>
          <div className="p-4 rounded-lg bg-surface-hover">
            <div className="text-sm text-muted font-medium">With per-user calibration (50+ samples)</div>
            <div className="text-2xl font-semibold tabular-nums text-neutral mt-2">F1: 0.55 – 0.70</div>
            <div className="text-xs text-muted mt-1.5">Estimated from Pepa et al. 2021 + personalization</div>
          </div>
          <div className="p-4 rounded-lg bg-surface-hover">
            <div className="text-sm text-muted font-medium">Lab study best (ETH Zurich 2023)</div>
            <div className="text-2xl font-semibold tabular-nums text-accent-light mt-2">F1: 0.625</div>
            <div className="text-xs text-muted mt-1.5">90 participants, simulated office, gradient boosting</div>
          </div>
          <div className="p-4 rounded-lg bg-surface-hover">
            <div className="text-sm text-muted font-medium">In-the-wild (Pepa et al. 2021)</div>
            <div className="text-2xl font-semibold tabular-nums text-accent-light mt-2">76%</div>
            <div className="text-xs text-muted mt-1.5">62 users, keyboard data, 3-class stress</div>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <h3 className="text-lg font-medium mb-5 text-white">How MindPulse works</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
          {[
            { step: "1", title: "Collect", desc: "Capture keyboard timing, mouse movements, app switches — never what you type" },
            { step: "2", title: "Extract", desc: "23 behavioral features per 5-minute window using sliding window analysis" },
            { step: "3", title: "Predict", desc: "XGBoost classifier trained on real behavioral data, normalized per-user" },
            { step: "4", title: "Insight", desc: "Stress score 0-100 with human-readable explanations of why" },
          ].map((s) => (
            <div key={s.step} className="p-4 rounded-lg bg-surface-hover">
              <div className="text-3xl font-bold text-accent/70 mb-2 tabular-nums">{s.step}</div>
              <div className="text-sm font-medium text-white mb-1.5">{s.title}</div>
              <div className="text-xs text-muted">{s.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Why Alert Fired */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <h3 className="text-lg font-medium mb-5 text-white">Alert status</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-surface-hover">
            <div className="text-sm text-muted font-medium">Current alert state</div>
            <div className="text-xl font-semibold mt-2 tabular-nums">{interventionSnapshot?.alert_state ?? "NORMAL"}</div>
          </div>
          <div className="p-4 rounded-lg bg-surface-hover">
            <div className="text-sm text-muted font-medium">Recent trend</div>
            <div className="text-xl font-semibold mt-2 tabular-nums">{interventionSnapshot?.trend ?? "steady"}</div>
          </div>
          <div className="p-4 rounded-lg bg-surface-hover">
            <div className="text-sm text-muted font-medium">Recovery score</div>
            <div className="text-xl font-semibold mt-2 tabular-nums text-neutral">
              {interventionSnapshot?.recovery_score ? `+${interventionSnapshot.recovery_score.toFixed(1)}` : "0.0"}
            </div>
          </div>
        </div>
        {interventionSnapshot?.intervention && (
          <div className="mt-4 p-4 rounded-lg bg-accent/[0.04] border border-accent/20">
            <div className="text-sm font-medium mb-2 text-white">{interventionSnapshot.intervention.title}</div>
            <ul className="space-y-1 text-xs text-muted">
              {interventionSnapshot.intervention.rationale.map((reason, i) => (
                <li key={i}>• {reason}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

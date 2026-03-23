"use client";

export default function InsightsPage() {
  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold">Insights</h1>
        <p className="text-sm text-muted mt-1">Understand what drives your stress scores</p>
      </div>

      {/* Feature Importance */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <h3 className="text-lg font-semibold mb-4">Top Stress Indicators (XGBoost Feature Importance)</h3>
        <div className="space-y-3">
          {[
            { name: "Session Fragmentation", pct: 35.6, desc: "How scattered your work sessions are" },
            { name: "Rage Click Count", pct: 27.6, desc: "Rapid frustrated clicking detected" },
            { name: "Switch Entropy", pct: 12.7, desc: "Randomness of app/tab switching" },
            { name: "Mouse Speed Std", pct: 4.6, desc: "Inconsistency of mouse movements" },
            { name: "Scroll Velocity Std", pct: 4.2, desc: "Erratic scrolling patterns" },
            { name: "Direction Change Rate", pct: 3.7, desc: "Cursor indecision / hesitation" },
            { name: "Rhythm Entropy", pct: 3.7, desc: "Chaos in typing rhythm" },
          ].map((f, i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="w-48 text-sm text-white">{f.name}</div>
              <div className="flex-1 h-4 bg-surface-hover rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent rounded-full transition-all"
                  style={{ width: `${f.pct * 100 / 35.6}%` }}
                />
              </div>
              <div className="w-12 text-right text-sm text-muted">{f.pct}%</div>
              <div className="w-64 text-xs text-muted">{f.desc}</div>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted mt-4">
          Our 3 novel features (session fragmentation, rage clicks, switch entropy) account for 75.9% of model decisions.
          Traditional keystroke features (hold/flight times) contribute only ~2%.
        </p>
      </div>

      {/* Research Context */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <h3 className="text-lg font-semibold mb-4">Research-Backed Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-surface-hover">
            <div className="text-sm text-muted">Universal Model (no calibration)</div>
            <div className="text-2xl font-bold text-mild mt-1">F1: 0.25 – 0.40</div>
            <div className="text-xs text-muted mt-1">Naegelin et al. 2025, 36 employees, 8-week field study</div>
          </div>
          <div className="p-4 rounded-lg bg-surface-hover">
            <div className="text-sm text-muted">With Per-User Calibration (50+ samples)</div>
            <div className="text-2xl font-bold text-neutral mt-1">F1: 0.55 – 0.70</div>
            <div className="text-xs text-muted mt-1">Estimated from Pepa et al. 2021 + personalization</div>
          </div>
          <div className="p-4 rounded-lg bg-surface-hover">
            <div className="text-sm text-muted">Lab Study Best (ETH Zurich 2023)</div>
            <div className="text-2xl font-bold text-accent mt-1">F1: 0.625</div>
            <div className="text-xs text-muted mt-1">90 participants, simulated office, gradient boosting</div>
          </div>
          <div className="p-4 rounded-lg bg-surface-hover">
            <div className="text-sm text-muted">In-the-Wild (Pepa et al. 2021)</div>
            <div className="text-2xl font-bold text-accent mt-1">76%</div>
            <div className="text-xs text-muted mt-1">62 users, keyboard data, 3-class stress</div>
          </div>
        </div>
        <p className="text-xs text-muted mt-4">
          Stress detection in real-world settings is fundamentally harder than lab conditions.
          The key insight from ETH Zurich 2025: "One does not fit all" — per-user calibration is essential.
        </p>
      </div>

      {/* How It Works */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <h3 className="text-lg font-semibold mb-4">How MindPulse Works</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[
            { step: "1", title: "Collect", desc: "Capture keyboard timing, mouse movements, app switches — never what you type" },
            { step: "2", title: "Extract", desc: "23 behavioral features per 5-minute window using sliding window analysis" },
            { step: "3", title: "Predict", desc: "XGBoost classifier trained on real behavioral data, normalized per-user" },
            { step: "4", title: "Insight", desc: "Stress score 0-100 with human-readable explanations of why" },
          ].map((s) => (
            <div key={s.step} className="p-4 rounded-lg bg-surface-hover">
              <div className="text-3xl font-bold text-accent mb-2">{s.step}</div>
              <div className="text-sm font-medium text-white mb-1">{s.title}</div>
              <div className="text-xs text-muted">{s.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import type { CalibrationStatus } from "@/lib/types";

export default function CalibrationPage() {
  const [status, setStatus] = useState<CalibrationStatus | null>(null);

  useEffect(() => {
    api.calibration().then(setStatus).catch(() => {});
  }, []);

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold">Calibration</h1>
        <p className="text-sm text-muted mt-1">Build your personal stress baseline for accurate detection</p>
      </div>

      {/* Why Calibration */}
      <div className="rounded-xl border border-accent/30 bg-accent/5 p-6">
        <h3 className="text-lg font-semibold mb-2">Why Calibration Matters</h3>
        <p className="text-sm text-muted">
          Stress is highly individual. A "universal" model achieves only 25-40% accuracy because
          each person types differently. By building your personal baseline over 7 days, MindPulse
          learns YOUR normal patterns and detects deviations — pushing accuracy to 55-70%.
        </p>
        <p className="text-xs text-muted mt-2">
          Source: ETH Zurich 2025 — "One does not fit all: personalised approaches show encouraging potential"
        </p>
      </div>

      {/* Calibration Progress */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <h3 className="text-lg font-semibold mb-4">Calibration Progress</h3>
        <div className="grid grid-cols-7 gap-2">
          {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, i) => {
            const collected = i < (status?.days_collected ?? 0);
            return (
              <div
                key={day}
                className={`p-3 rounded-lg text-center text-sm ${
                  collected ? "bg-neutral/20 text-neutral border border-neutral/30" : "bg-surface-hover text-muted border border-border"
                }`}
              >
                <div className="text-xs">{day}</div>
                <div className="text-lg mt-1">{collected ? "✓" : "○"}</div>
              </div>
            );
          })}
        </div>
        <div className="mt-4">
          <div className="flex justify-between text-xs text-muted mb-1">
            <span>Progress</span>
            <span>{status?.completion_pct ?? 0}%</span>
          </div>
          <div className="h-2 bg-surface-hover rounded-full overflow-hidden">
            <div className="h-full bg-accent rounded-full transition-all" style={{ width: `${status?.completion_pct ?? 0}%` }} />
          </div>
        </div>
      </div>

      {/* Hourly Coverage */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <h3 className="text-lg font-semibold mb-4">Hourly Coverage</h3>
        <p className="text-xs text-muted mb-4">
          MindPulse needs samples across different hours to build your circadian profile.
          Aim for at least 20 samples per hour you typically work.
        </p>
        <div className="grid grid-cols-12 gap-1">
          {Array.from({ length: 24 }, (_, h) => {
            const samples = status?.samples_per_hour?.[h] ?? 0;
            const opacity = Math.min(samples / 50, 1);
            return (
              <div
                key={h}
                className="p-2 rounded text-center text-xs"
                style={{ background: `rgba(108, 92, 231, ${opacity * 0.5})` }}
                title={`${h}:00 — ${samples} samples`}
              >
                {h}
              </div>
            );
          })}
        </div>
        <div className="flex items-center gap-2 mt-3 text-xs text-muted">
          <div className="w-3 h-3 rounded" style={{ background: "rgba(108,92,231,0.1)" }} />
          Few samples
          <div className="w-3 h-3 rounded" style={{ background: "rgba(108,92,231,0.5)" }} />
          Good coverage
        </div>
      </div>

      {/* Instructions */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <h3 className="text-lg font-semibold mb-4">How to Calibrate</h3>
        <ol className="space-y-3 text-sm text-muted">
          <li className="flex gap-3">
            <span className="text-accent font-bold">1.</span>
            <span>Use MindPulse during your normal work hours for 7 days</span>
          </li>
          <li className="flex gap-3">
            <span className="text-accent font-bold">2.</span>
            <span>Self-report your stress level every 30 minutes (builds ground truth)</span>
          </li>
          <li className="flex gap-3">
            <span className="text-accent font-bold">3.</span>
            <span>Work at least 2 hours per day with tracking enabled</span>
          </li>
          <li className="flex gap-3">
            <span className="text-accent font-bold">4.</span>
            <span>After 7 days, your personal model activates automatically</span>
          </li>
        </ol>
      </div>
    </div>
  );
}

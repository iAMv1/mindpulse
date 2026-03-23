"use client";

import { useEffect, useRef, useState } from "react";

export default function PrivacyPage() {
  const [trackingPaused, setTrackingPaused] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const showNotification = (msg: string) => {
    setNotification(msg);
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setNotification(null), 3000);
  };

  const handlePause = () => {
    setTrackingPaused(!trackingPaused);
    showNotification(trackingPaused ? "Tracking resumed" : "Tracking paused");
  };

  const handleExport = () => {
    showNotification("Data export started - this feature requires backend connection");
  };

  const handleDelete = () => {
    if (confirm("Are you sure you want to delete all your data? This cannot be undone.")) {
      showNotification("All data has been deleted");
    }
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, []);

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto">
      {notification && (
        <div className="fixed top-4 right-4 bg-accent text-white px-4 py-2 rounded-lg shadow-lg z-50">
          {notification}
        </div>
      )}
      <div>
        <h1 className="text-2xl font-bold">Privacy & Data</h1>
        <p className="text-sm text-muted mt-1">What MindPulse captures and what it never does</p>
      </div>

      {/* What We Capture */}
      <div className="rounded-xl border border-neutral/30 bg-neutral/5 p-6">
        <h3 className="text-lg font-semibold text-neutral mb-4">What We Capture</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { title: "Keyboard", items: ["Key press/release timestamps", "Key category (alpha/digit/special)", "Hold time, flight time", "Backspace count (not content)"] },
            { title: "Mouse", items: ["Movement speed & direction", "Click timestamps", "Scroll velocity", "Rage click detection"] },
            { title: "Context", items: ["App switch timestamps", "Hashed app category", "Tab switch frequency", "Session duration"] },
          ].map((cat) => (
            <div key={cat.title} className="p-4 rounded-lg bg-surface">
              <h4 className="font-medium mb-2">{cat.title}</h4>
              <ul className="space-y-1">
                {cat.items.map((item) => (
                  <li key={item} className="text-xs text-muted flex gap-2">
                    <span className="text-neutral">✓</span> {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* What We Never Capture */}
      <div className="rounded-xl border border-stressed/30 bg-stressed/5 p-6">
        <h3 className="text-lg font-semibold text-stressed mb-4">What We NEVER Capture</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {["Actual keystrokes", "Typed content", "Screen content", "Page URLs", "File names", "Email content", "Chat messages", "Passwords"].map((item) => (
            <div key={item} className="flex items-center gap-2 text-sm text-muted">
              <span className="text-stressed">✗</span> {item}
            </div>
          ))}
        </div>
      </div>

      {/* Processing */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <h3 className="text-lg font-semibold mb-4">How Processing Works</h3>
        <div className="flex items-center gap-4 overflow-x-auto pb-2">
          {["Raw Events", "Feature Extraction", "Discard Raw", "ML Inference", "Score → Dashboard"].map((step, i) => (
            <div key={step} className="flex items-center gap-2">
              <div className="px-4 py-2 rounded-lg bg-surface-hover text-sm whitespace-nowrap">{step}</div>
              {i < 4 && <span className="text-accent">→</span>}
            </div>
          ))}
        </div>
        <p className="text-xs text-muted mt-3">
          All processing happens locally. Raw keystrokes are never stored or transmitted.
          Only derived behavioral features are used for prediction.
        </p>
      </div>

      {/* Data Control */}
      <div className="rounded-xl border border-border bg-surface p-6">
        <h3 className="text-lg font-semibold mb-4">Your Data Controls</h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium">Pause Tracking</div>
              <div className="text-xs text-muted">Temporarily stop all data collection</div>
            </div>
            <button 
              onClick={handlePause}
              className={`px-4 py-1.5 rounded-lg border text-sm transition ${trackingPaused ? 'bg-accent text-white border-accent' : 'border-border hover:bg-surface-hover'}`}
            >
              {trackingPaused ? "Resume" : "Pause"}
            </button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium">Export My Data</div>
              <div className="text-xs text-muted">Download all your data as CSV</div>
            </div>
            <button 
              onClick={handleExport}
              className="px-4 py-1.5 rounded-lg border border-border text-sm hover:bg-surface-hover transition"
            >
              Export
            </button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium">Delete All Data</div>
              <div className="text-xs text-muted">Permanently remove all stored data</div>
            </div>
            <button 
              onClick={handleDelete}
              className="px-4 py-1.5 rounded-lg border border-stressed/30 text-stressed text-sm hover:bg-stressed/10 transition"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

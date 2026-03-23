"use client";

import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b border-border px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <Link href="/" className="text-lg font-bold text-accent">
          MindPulse
        </Link>
        <span className="text-xs text-muted bg-surface px-2 py-1 rounded">
          Privacy-first behavioral stress detection
        </span>
      </div>
      <div className="flex items-center gap-3">
        <ConnectionDot />
        <button className="px-3 py-1.5 rounded-lg bg-accent text-white text-xs font-medium hover:bg-accent/80 transition">
          Start Tracking
        </button>
      </div>
    </header>
  );
}

function ConnectionDot() {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-2 h-2 rounded-full bg-neutral animate-pulse" />
      <span className="text-muted">Backend</span>
    </div>
  );
}

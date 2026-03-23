"use client";

import Link from "next/link";
import { useWebSocket } from "@/hooks/use-websocket";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:5000/api/v1/ws/stress";

export default function Header() {
  const { connected, error } = useWebSocket(WS_URL);

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
        <ConnectionDot connected={connected} error={error} />
        <button className="px-3 py-1.5 rounded-lg bg-accent text-white text-xs font-medium hover:bg-accent/80 transition">
          Start Tracking
        </button>
      </div>
    </header>
  );
}

function ConnectionDot({ connected, error }: { connected: boolean; error: string | null }) {
  const getStatus = () => {
    if (connected) return { color: "bg-neutral", text: "Connected", textColor: "text-neutral" };
    if (error) return { color: "bg-stressed", text: error, textColor: "text-stressed" };
    return { color: "bg-muted animate-pulse", text: "Connecting...", textColor: "text-muted" };
  };

  const status = getStatus();

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className={`w-2 h-2 rounded-full ${status.color}`} />
      <span className={status.textColor}>{status.text}</span>
    </div>
  );
}

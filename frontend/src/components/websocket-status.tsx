"use client";

interface WebSocketStatusProps {
  connected: boolean;
  error: string | null;
}

export function WebSocketStatus({ connected, error }: WebSocketStatusProps) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span
        className={`w-2 h-2 rounded-full ${
          connected ? "bg-neutral animate-pulse" : "bg-stressed"
        }`}
      />
      <span className={connected ? "text-neutral" : "text-stressed"}>
        {connected ? "Live" : error || "Disconnected"}
      </span>
    </div>
  );
}

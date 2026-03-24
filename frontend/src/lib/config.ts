const DEFAULT_WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:5000/api/v1/ws/stress";

export function resolveWsUrl(): string {
  if (typeof window === "undefined") return DEFAULT_WS_URL;
  if (process.env.NEXT_PUBLIC_WS_URL) return process.env.NEXT_PUBLIC_WS_URL;
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}/api/v1/ws/stress`;
}

export const WS_URL = DEFAULT_WS_URL;

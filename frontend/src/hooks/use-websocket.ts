"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type { HistoryPoint } from "@/lib/types";

export interface StressData {
  score: number;
  level: "NEUTRAL" | "MILD" | "STRESSED";
  confidence: number;
  probabilities: { NEUTRAL: number; MILD: number; STRESSED: number };
  features: {
    typing_speed_wpm: number;
    error_rate: number;
    rage_click_count: number;
    tab_switch_freq: number;
    rhythm_entropy: number;
    session_fragmentation: number;
  };
  timestamp: number;
}

interface UseWebSocketReturn {
  data: StressData | null;
  history: HistoryPoint[];
  connected: boolean;
  error: string | null;
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [data, setData] = useState<StressData | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  // prevents state updates and retries after unmount to avoid leaks/console warnings
  const shouldReconnect = useRef(true);

  const connect = useCallback(() => {
    if (!shouldReconnect.current) return;
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        if (!shouldReconnect.current) return;
        setConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "stress_update") {
            if (!shouldReconnect.current) return;
            const stressData: StressData = {
              score: msg.score,
              level: msg.level,
              confidence: msg.confidence,
              probabilities: msg.probabilities,
              features: msg.features,
              timestamp: Date.now(),
            };
            setData(stressData);
            setHistory((prev) => [
              ...prev.slice(-120),
              { timestamp: stressData.timestamp, score: stressData.score, level: stressData.level, insights: [] },
            ]);
          }
        } catch {}
      };

      ws.onclose = () => {
        if (!shouldReconnect.current) return;
        setConnected(false);
        reconnectTimer.current = setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        if (!shouldReconnect.current) return;
        setError("Connection failed");
        ws.close();
      };

      wsRef.current = ws;
    } catch (e) {
      if (shouldReconnect.current) {
        setError("WebSocket unavailable");
      }
    }
  }, [url]);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();
    return () => {
      shouldReconnect.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { data, history, connected, error };
}

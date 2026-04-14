"use client";

import { useState, useEffect, useRef, useCallback } from "react";

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

export interface HistoryPoint {
  timestamp: number;
  score: number;
  level: string;
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
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        reconnectAttemptsRef.current = 0;
        setConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "ping") {
            ws.send(JSON.stringify({ type: "pong", timestamp: Date.now() }));
            return;
          }
          if (msg.type === "stress_update") {
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
              { timestamp: stressData.timestamp, score: stressData.score, level: stressData.level },
            ]);
          }
        } catch {}
      };

      ws.onclose = () => {
        setConnected(false);
        reconnectAttemptsRef.current += 1;
        const jitter = Math.floor(Math.random() * 800);
        const backoff = Math.min(
          10000,
          2000 + reconnectAttemptsRef.current * 500 + jitter,
        );
        reconnectTimer.current = setTimeout(connect, backoff);
      };

      ws.onerror = () => {
        setError("Connection failed");
        ws.close();
      };

      wsRef.current = ws;
    } catch (e) {
      setError("WebSocket unavailable");
    }
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
      }
      wsRef.current?.close();
    };
  }, [connect]);

  return { data, history, connected, error };
}

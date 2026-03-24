/** MindPulse — WebSocket Hook */

"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type { StressResult } from "@/lib/types";
import { resolveWsUrl } from "@/lib/config";

type ConnectionStatus = "connected" | "connecting" | "disconnected";

interface UseStressStreamReturn {
  data: StressResult | null;
  history: StressResult[];
  status: ConnectionStatus;
  send: (features: Record<string, number>, userId?: string) => void;
  reconnect: () => void;
}

export function useStressStream(): UseStressStreamReturn {
  const [data, setData] = useState<StressResult | null>(null);
  const [history, setHistory] = useState<StressResult[]>([]);
  const [status, setStatus] = useState<ConnectionStatus>("disconnected");
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<NodeJS.Timeout | null>(null);
  const manualClose = useRef(false);
  const shouldReconnect = useRef(true);

  const connect = useCallback(() => {
    if (!shouldReconnect.current) return;
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    try {
      setStatus("connecting");
      const ws = new WebSocket(resolveWsUrl());
      ws.onopen = () => shouldReconnect.current && setStatus("connected");
      ws.onclose = () => {
        if (manualClose.current) {
          manualClose.current = false;
          setStatus("disconnected");
          return;
        }
        if (!shouldReconnect.current) return;
        setStatus("disconnected");
        reconnectTimer.current = setTimeout(connect, 3000);
      };
      ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === "stress_update") {
            if (!shouldReconnect.current) return;
            const result: StressResult = {
              score: msg.score,
              level: msg.level,
              confidence: msg.confidence,
              probabilities: msg.probabilities,
              insights: msg.insights || [],
              timestamp: msg.timestamp || Date.now(),
            };
            setData(result);
            setHistory((prev) => [...prev.slice(-120), result]);
          }
        } catch {}
      };
      ws.onerror = () => ws.close();
      wsRef.current = ws;
    } catch {
      if (shouldReconnect.current) {
        setStatus("disconnected");
      }
    }
  }, []);

  useEffect(() => {
    connect();
    return () => {
      shouldReconnect.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((features: Record<string, number>, userId: string = "default") => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "features", features, user_id: userId }));
    }
  }, []);

  const reconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      return;
    }
    if (wsRef.current) {
      manualClose.current = true;
      wsRef.current.close();
    }
    connect();
  }, [connect]);

  return { data, history, status, send, reconnect };
}

/** MindPulse — API Client */

import type { FeatureVector, StressResult, HistoryPoint, CalibrationStatus, UserStats, HealthStatus } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5000/api/v1";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY;

const STORAGE_KEY = "mindpulse_user_id";

export function getUserId(): string {
  if (typeof window === "undefined") return "default";
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) return stored;
  const newId = `user_${Date.now()}`;
  localStorage.setItem(STORAGE_KEY, newId);
  return newId;
}

export function setUserId(id: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(STORAGE_KEY, id);
  }
}

export function getAvailableUsers(): string[] {
  if (typeof window === "undefined") return ["default"];
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored ? [stored] : ["default"];
}

function buildHeaders(options?: RequestInit): Headers {
  const headers = new Headers();
  headers.set("Content-Type", "application/json");

  if (API_KEY) {
    headers.set("X-API-Key", API_KEY);
  }

  if (options?.headers) {
    new Headers(options.headers).forEach((value, key) => {
      headers.set(key, value);
    });
  }

  return headers;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: buildHeaders(options),
  });
  if (!res.ok) {
    const error = `API error: ${res.status}`;
    console.error(error);
    throw new Error(error);
  }
  return res.json();
}

export const api = {
  health: async () => {
    try {
      return await request<HealthStatus>("/health");
    } catch (error) {
      console.error("Health check failed:", error);
      throw error;
    }
  },

  inference: async (features: FeatureVector, userId?: string) => {
    const uid = userId || getUserId();
    try {
      return await request<StressResult>("/inference", {
        method: "POST",
        body: JSON.stringify({ features, user_id: uid }),
      });
    } catch (error) {
      console.error("Inference failed:", error);
      throw error;
    }
  },

  history: async (userId?: string, hours: number = 24) => {
    const uid = userId || getUserId();
    try {
      return await request<HistoryPoint[]>(`/history?user_id=${uid}&hours=${hours}`);
    } catch (error) {
      console.error("History fetch failed:", error);
      throw error;
    }
  },

  stats: async (userId?: string) => {
    const uid = userId || getUserId();
    try {
      return await request<UserStats>(`/stats?user_id=${uid}`);
    } catch (error) {
      console.error("Stats fetch failed:", error);
      throw error;
    }
  },

  calibration: async (userId?: string) => {
    const uid = userId || getUserId();
    try {
      return await request<CalibrationStatus>(`/calibration/${uid}`);
    } catch (error) {
      console.error("Calibration fetch failed:", error);
      throw error;
    }
  },

  feedback: async (predicted: string, actual: string, userId?: string) => {
    const uid = userId || getUserId();
    try {
      return await request("/feedback", {
        method: "POST",
        body: JSON.stringify({ user_id: uid, predicted_level: predicted, actual_level: actual, timestamp: Date.now() }),
      });
    } catch (error) {
      console.error("Feedback submission failed:", error);
      throw error;
    }
  },
};

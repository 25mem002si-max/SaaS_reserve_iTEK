import type { Reservation, RestaurantTable } from "./types";
import { getToken } from "./auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status} on ${path}`);
  }

  return res.json() as Promise<T>;
}

export function fetchTables(): Promise<RestaurantTable[]> {
  return apiFetch<RestaurantTable[]>("/tables");
}

export function fetchReservations(): Promise<Reservation[]> {
  return apiFetch<Reservation[]>("/reservations");
}

export function toggleAgent(enabled: boolean): Promise<{ enabled: boolean }> {
  return apiFetch("/settings/agent", {
    method: "PATCH",
    body: JSON.stringify({ enabled }),
  });
}

export function fetchAttendanceStats(): Promise<{ day: string; guests: number }[]> {
  return apiFetch("/analytics/attendance");
}

export function fetchPopularDishes(): Promise<{ name: string; value: number }[]> {
  return apiFetch("/analytics/popular-dishes");
}

export function fetchRevenueForecast(): Promise<{ month: string; revenue: number }[]> {
  return apiFetch("/analytics/revenue-forecast");
}

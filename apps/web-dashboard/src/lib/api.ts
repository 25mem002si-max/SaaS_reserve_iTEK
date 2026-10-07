import type { Reservation, RestaurantTable } from "./types";
import type { AnalyticsPeriod } from "./analytics";
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

// Les 3 fonctions ci-dessous prennent desormais une `period` (ex: "7d",
// "30d", "90d" — voir src/lib/analytics.ts) et la transmettent au backend
// via un parametre de requete `?period=...`. C'est le backend (API du Dev
// 2) qui doit interpreter cette valeur pour filtrer/agreger les donnees en
// consequence — a synchroniser avec lui : nom exact du parametre et
// valeurs acceptees doivent correspondre EXACTEMENT des deux cotes.
export function fetchAttendanceStats(
  period: AnalyticsPeriod
): Promise<{ day: string; guests: number }[]> {
  return apiFetch(`/analytics/attendance?period=${period}`);
}

export function fetchPopularDishes(
  period: AnalyticsPeriod
): Promise<{ name: string; value: number }[]> {
  return apiFetch(`/analytics/popular-dishes?period=${period}`);
}

export function fetchRevenueForecast(
  period: AnalyticsPeriod
): Promise<{ month: string; revenue: number }[]> {
  return apiFetch(`/analytics/revenue-forecast?period=${period}`);
}

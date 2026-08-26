import { useEffect, useState } from "react";
import { fetchReservations } from "@/lib/api";
import type { Reservation } from "@/lib/types";

export function useReservations() {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetchReservations()
      .then(setReservations)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { reservations, loading, error };
}

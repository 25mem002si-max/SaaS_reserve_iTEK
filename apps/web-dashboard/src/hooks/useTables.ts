import { useEffect, useState } from "react";
import { fetchTables } from "@/lib/api";
import type { RestaurantTable } from "@/lib/types";

export function useTables() {
  const [tables, setTables] = useState<RestaurantTable[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTables()
      .then(setTables)
      .finally(() => setLoading(false));
  }, []);

  return { tables, loading };
}

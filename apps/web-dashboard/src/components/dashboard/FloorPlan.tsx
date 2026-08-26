"use client";

import { useEffect, useState } from "react";
import { getSocket } from "@/lib/websocket";
import { fetchTables } from "@/lib/api";
import TableCard from "./TableCard";
import type { RestaurantTable } from "@/lib/types";

// Vue synoptique de la salle : recupere les tables via REST, puis se met a
// jour en temps reel via WebSocket lorsque le statut d'une table change
// (nouvelle reservation, verrou Redis, liberation...).
export default function FloorPlan() {
  const [tables, setTables] = useState<RestaurantTable[]>([]);

  useEffect(() => {
    fetchTables().then(setTables).catch(console.error);

    const socket = getSocket();
    socket.on("table_status_update", (updated: RestaurantTable) => {
      setTables((prev) =>
        prev.map((t) => (t.id === updated.id ? updated : t))
      );
    });

    return () => {
      socket.off("table_status_update");
    };
  }, []);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
      {tables.map((table) => (
        <TableCard key={table.id} table={table} />
      ))}
      {tables.length === 0 && (
        <p className="text-gray-500 text-sm col-span-full">
          Aucune table configuree pour le moment.
        </p>
      )}
    </div>
  );
}

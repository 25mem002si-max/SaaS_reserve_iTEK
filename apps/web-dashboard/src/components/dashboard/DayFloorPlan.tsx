"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchTables, fetchReservations } from "@/lib/api";
import TableCard from "./TableCard";
import TableDetailsModal from "./TableDetailsModal";
import type { Reservation, RestaurantTable } from "@/lib/types";

// Convertit une date ISO (ex: "2026-08-26T14:00:00.000Z") en cle "YYYY-MM-DD"
// en heure LOCALE (pas UTC), pour comparer deux dates "jour uniquement" sans
// se soucier de l'heure exacte de la reservation.
function toDayKey(isoDate: string): string {
  const d = new Date(isoDate);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

// DayFloorPlan = variante de FloorPlan.tsx (vue de la salle) mais figee sur
// UNE journee precise, passee en prop `date` (format "YYYY-MM-DD") depuis
// l'URL /dashboard/reservations/[date].
//
// Difference cle avec FloorPlan : ici on ne se connecte PAS au WebSocket.
// Le statut affiche n'est pas "en direct", c'est une reconstitution de la
// situation du jour choisi, calculee a partir des reservations qui tombent
// ce jour-la :
//   - une table avec au moins une reservation ce jour -> RESERVED
//   - une table sans reservation ce jour               -> FREE
// On ignore volontairement les statuts "temps reel" OCCUPIED/LOCKED de
// l'API /tables, qui n'ont de sens que pour l'instant present.
export default function DayFloorPlan({ date }: { date: string }) {
  const [tables, setTables] = useState<RestaurantTable[]>([]);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [selectedTable, setSelectedTable] = useState<RestaurantTable | null>(null);

  useEffect(() => {
    fetchTables().then(setTables).catch(console.error);
    fetchReservations().then(setReservations).catch(console.error);
  }, []);

  const reservationsForDay = reservations.filter(
    (r) => toDayKey(r.reservation_date) === date
  );

  const tablesForDay: RestaurantTable[] = tables.map((table) => {
    const hasReservationThisDay = reservationsForDay.some(
      (r) => r.table_id === table.id
    );
    return { ...table, status: hasReservationThisDay ? "RESERVED" : "FREE" };
  });

  const reservationForSelectedTable =
    reservationsForDay.find((r) => r.table_id === selectedTable?.id) ?? null;

  return (
    <div className="space-y-4">
      <Link
        href="/dashboard/reservations"
        className="text-sm text-primary hover:underline"
      >
        ← Retour au calendrier
      </Link>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {tablesForDay.map((table) => (
          <TableCard key={table.id} table={table} onClick={setSelectedTable} />
        ))}
        {tablesForDay.length === 0 && (
          <p className="text-gray-500 text-sm col-span-full">
            Aucune table configuree pour le moment.
          </p>
        )}
      </div>

      {/*
        On reutilise TableDetailsModal SANS AUCUNE MODIFICATION : il affiche
        deja "table libre" quand reservation est null, et les details complets
        sinon. Pas besoin de creer un composant de modale different.
      */}
      <TableDetailsModal
        table={selectedTable}
        reservation={reservationForSelectedTable}
        onClose={() => setSelectedTable(null)}
      />
    </div>
  );
}
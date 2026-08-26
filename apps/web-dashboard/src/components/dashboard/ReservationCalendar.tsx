"use client";

import { useEffect, useState } from "react";
import { Calendar, dateFnsLocalizer } from "react-big-calendar";
import format from "date-fns/format";
import parse from "date-fns/parse";
import startOfWeek from "date-fns/startOfWeek";
import getDay from "date-fns/getDay";
import fr from "date-fns/locale/fr";
import "react-big-calendar/lib/css/react-big-calendar.css";
import { fetchReservations, fetchTables } from "@/lib/api";
import ReservationDetailsModal from "./ReservationDetailsModal";
import type { Reservation, RestaurantTable } from "@/lib/types";

// react-big-calendar a besoin d'un "localizer" pour savoir comment
// formater les dates/heures et sur quel jour commence la semaine (lundi en
// France/RDC, contrairement aux Etats-Unis ou c'est dimanche).
const locales = { fr };
const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: () => startOfWeek(new Date(), { locale: fr }),
  getDay,
  locales,
});

// Type d'un "evenement" tel que react-big-calendar les attend : un titre a
// afficher, une date de debut/fin, et un champ libre `resource` dans lequel
// on range la reservation complete pour pouvoir la retrouver au clic.
interface CalendarEvent {
  title: string;
  start: Date;
  end: Date;
  resource: Reservation;
}

// Calendrier des reservations (issu de la table `reservations` PostgreSQL).
export default function ReservationCalendar() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [tables, setTables] = useState<RestaurantTable[]>([]);
  const [selectedReservation, setSelectedReservation] = useState<Reservation | null>(null);

  useEffect(() => {
    fetchReservations().then((reservations: Reservation[]) => {
      setEvents(
        reservations.map((r) => ({
          title: `${r.customer_name} (${r.guests_count} pers.)`,
          start: new Date(r.reservation_date),
          end: new Date(r.reservation_date),
          resource: r,
        }))
      );
    });

    fetchTables().then(setTables).catch(console.error);
  }, []);

  const tableForSelectedReservation =
    tables.find((t) => t.id === selectedReservation?.table_id) ?? null;

  return (
    <>
      <div className="bg-white rounded-xl p-4 shadow" style={{ height: 600 }}>
        <Calendar
          localizer={localizer}
          events={events}
          startAccessor="start"
          endAccessor="end"
          culture="fr"
          onSelectEvent={(event: CalendarEvent) => setSelectedReservation(event.resource)}
        />
      </div>

      <ReservationDetailsModal
        reservation={selectedReservation}
        table={tableForSelectedReservation}
        onClose={() => setSelectedReservation(null)}
      />
    </>
  );
}
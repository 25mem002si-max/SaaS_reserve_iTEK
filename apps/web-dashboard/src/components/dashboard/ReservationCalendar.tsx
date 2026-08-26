"use client";

import { useEffect, useState } from "react";
import { Calendar, dateFnsLocalizer } from "react-big-calendar";
import format from "date-fns/format";
import parse from "date-fns/parse";
import startOfWeek from "date-fns/startOfWeek";
import getDay from "date-fns/getDay";
import fr from "date-fns/locale/fr";
import "react-big-calendar/lib/css/react-big-calendar.css";
import { fetchReservations } from "@/lib/api";
import type { Reservation } from "@/lib/types";

const locales = { fr };
const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: () => startOfWeek(new Date(), { locale: fr }),
  getDay,
  locales,
});

// Calendrier des reservations (issu de la table `reservations` PostgreSQL)
export default function ReservationCalendar() {
  const [events, setEvents] = useState<any[]>([]);

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
  }, []);

  return (
    <div className="bg-white rounded-xl p-4 shadow" style={{ height: 600 }}>
      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        culture="fr"
      />
    </div>
  );
}

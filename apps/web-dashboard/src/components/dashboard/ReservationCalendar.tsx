"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Calendar, dateFnsLocalizer } from "react-big-calendar";
import { format } from "date-fns/format";
import { parse } from "date-fns/parse";
import { startOfWeek } from "date-fns/startOfWeek";
import { getDay } from "date-fns/getDay";
import { fr } from "date-fns/locale/fr";
import "react-big-calendar/lib/css/react-big-calendar.css";
import { fetchReservations, fetchTables } from "@/lib/api";
import ReservationDetailsModal from "./ReservationDetailsModal";
import type { Reservation, RestaurantTable } from "@/lib/types";

const locales = { fr };
const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: () => startOfWeek(new Date(), { locale: fr }),
  getDay,
  locales,
});

interface CalendarEvent {
  title: string;
  start: Date;
  end: Date;
  resource: Reservation;
}

export default function ReservationCalendar() {
  // useRouter (next/navigation, App Router) permet de naviguer vers une
  // autre page en JavaScript, sans recharger toute la page - utilise ici
  // pour aller sur /dashboard/reservations/[date] au clic sur un jour.
  const router = useRouter();

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
          // `selectable` active la detection de clic sur une case de jour
          // VIDE (sans evenement dessus). Sans cette prop, onSelectSlot ne
          // serait jamais declenche.
          selectable
          // onSelectSlot : declenche quand on clique sur une case de jour du
          // calendrier (en dehors d'un evenement existant). `slotInfo.start`
          // contient la date du jour cliqué. On la formate en "YYYY-MM-DD"
          // (avec la fonction `format` de date-fns deja importee plus haut)
          // et on navigue vers la page dediee a ce jour.
          onSelectSlot={(slotInfo: { start: Date }) => {
            const dayKey = format(slotInfo.start, "yyyy-MM-dd");
            router.push(`/dashboard/reservations/${dayKey}`);
          }}
          // onSelectEvent : callback fourni par react-big-calendar, appele
          // avec l'evenement cliqué (donc un clic PRECISEMENT sur la barre
          // "Jean Kabila (4 pers.)", pas sur la case de jour). On recupere
          // `event.resource` (la reservation complete qu'on avait rangee
          // dedans plus haut) pour ouvrir la modale de detail existante -
          // ce comportement ne change pas.
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
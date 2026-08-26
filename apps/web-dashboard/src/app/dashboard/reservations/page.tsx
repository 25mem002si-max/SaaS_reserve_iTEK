import ReservationCalendar from "@/components/dashboard/ReservationCalendar";

export default function ReservationsPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Reservations</h1>
      <ReservationCalendar />
    </div>
  );
}

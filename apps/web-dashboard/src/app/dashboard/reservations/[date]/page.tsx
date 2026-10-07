import DayFloorPlan from "@/components/dashboard/DayFloorPlan";

// IMPORTANT (Next.js 15+/16) : dans les versions recentes de Next.js,
// `params` est devenu une PROMESSE (avant, dans Next 14, c'etait un objet
// simple directement utilisable). Il faut donc :
//   1. declarer le composant comme `async function`
//   2. faire `await params` avant de lire `params.date`
// Sans le `await`, `params` reste un objet Promise non resolu : essayer de
// lire `.date` dessus ou de le passer a `new Date(...)` produit "Invalid
// Date", exactement le bug observe.
export default async function ReservationsByDayPage({
  params,
}: {
  params: Promise<{ date: string }>;
}) {
  const { date } = await params;

  const formatted = new Date(`${date}T00:00:00`).toLocaleDateString("fr-FR", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold capitalize">
        Vue de la salle - {formatted}
      </h1>
      <DayFloorPlan date={date} />
    </div>
  );
}
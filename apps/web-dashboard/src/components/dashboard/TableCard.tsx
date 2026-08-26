import clsx from "clsx";
import type { RestaurantTable } from "@/lib/types";

const statusColor: Record<string, string> = {
  FREE: "bg-success/10 border-success text-success",
  RESERVED: "bg-accent/10 border-accent text-accent",
  OCCUPIED: "bg-danger/10 border-danger text-danger",
  LOCKED: "bg-gray-200 border-gray-400 text-gray-600",
};

export default function TableCard({ table }: { table: RestaurantTable }) {
  const color = statusColor[table.status] ?? statusColor.FREE;
  return (
    <div className={clsx("rounded-xl border p-3 text-center", color)}>
      <p className="font-semibold">Table {table.number_label}</p>
      <p className="text-xs">{table.capacity} places - {table.zone}</p>
      <p className="text-xs mt-1 font-medium">{table.status}</p>
    </div>
  );
}

import Link from "next/link";

const links = [
  { href: "/dashboard", label: "Salle" },
  { href: "/dashboard/reservations", label: "Reservations" },
  { href: "/dashboard/analytics", label: "Analytics" },
  { href: "/dashboard/settings", label: "Parametres" },
];

export default function Sidebar() {
  return (
    <aside className="w-56 shrink-0 bg-primary text-white p-4 hidden md:block">
      <h2 className="font-bold text-lg mb-6">SaaS Reservation IA</h2>
      <nav className="space-y-2">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="block rounded-lg px-3 py-2 text-sm hover:bg-primary-light/30"
          >
            {link.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}

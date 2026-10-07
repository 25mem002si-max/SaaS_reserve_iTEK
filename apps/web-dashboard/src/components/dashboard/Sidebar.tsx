"use client";
// "use client" est obligatoire ici : ce composant a besoin de savoir sur
// quelle URL on se trouve actuellement (usePathname), ce qui n'est possible
// que cote navigateur.

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";

const links = [
  { href: "/dashboard", label: "Salle" },
  { href: "/dashboard/reservations", label: "Reservations" },
  { href: "/dashboard/analytics", label: "Analytics" },
  { href: "/dashboard/settings", label: "Parametres" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 bg-primary text-white p-4 hidden md:block">
      <h2 className="font-bold text-lg mb-6">SaaS Reservation IA</h2>
      <nav className="space-y-2">
        {links.map((link) => {
          const isActive =
            link.href === "/dashboard"
              ? pathname === "/dashboard"
              : pathname === link.href || pathname.startsWith(`${link.href}/`);

          return (
            <Link
              key={link.href}
              href={link.href}
              className={clsx(
                "block rounded-lg px-3 py-2 text-sm transition",
                isActive
                  ? "bg-white/15 font-semibold"
                  : "hover:bg-primary-light/30"
              )}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
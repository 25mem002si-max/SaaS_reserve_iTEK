"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearAdminToken, getAdminToken } from "@/lib/admin-auth";

// ============================================================================
// AdminShell : cadre commun de toutes les pages /admin
// ============================================================================
// - Sur /admin/login : affiche simplement la page (pas de menu).
// - Sur les autres pages : verifie qu'un jeton admin existe. Sinon, renvoie
//   vers /admin/login AVANT d'afficher quoi que ce soit.
//
// Rappel : cette verification est un confort d'affichage. La securite reelle
// est assuree par le serveur, qui refuse les routes /admin/... sans jeton
// admin valide. Si le jeton a expire, les composants recoivent une erreur
// AdminAuthError et renvoient eux aussi vers la connexion.
export default function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isLoginPage = pathname === "/admin/login";
  // null = verification pas encore faite (premier rendu).
  const [allowed, setAllowed] = useState<boolean | null>(null);

  useEffect(() => {
    if (isLoginPage) return;
    if (getAdminToken()) setAllowed(true);
    else {
      setAllowed(false);
      // replace (et non push) : le bouton Precedent ne ramene pas sur une
      // page admin vide.
      router.replace("/admin/login");
    }
  }, [isLoginPage, router, pathname]);

  if (isLoginPage) return <>{children}</>;
  // Pendant la verification ou la redirection : rien de sensible a l'ecran.
  if (!allowed) return <p className="p-8 text-sm text-gray-500" role="status">Verification de la session...</p>;

  function logout() {
    clearAdminToken();
    router.replace("/admin/login");
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-gray-900 text-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex items-center gap-6">
            <span className="font-bold">Administration</span>
            <nav className="flex gap-4 text-sm">
              <Link href="/admin/restaurants" className={pathname.startsWith("/admin/restaurants") ? "font-semibold underline underline-offset-4" : "text-white/80 hover:text-white"}>
                Restaurants
              </Link>
              {/* Ouvre l'accueil public dans un nouvel onglet pour verifier le carrousel. */}
              <a href="/" target="_blank" rel="noreferrer" className="text-white/80 hover:text-white">
                Voir l&apos;accueil ↗
              </a>
            </nav>
          </div>
          <button type="button" onClick={logout} className="rounded-full border border-white/30 px-4 py-1.5 text-sm hover:bg-white/10">
            Deconnexion
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">{children}</main>
    </div>
  );
}

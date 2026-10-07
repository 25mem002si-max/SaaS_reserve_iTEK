import Link from "next/link";

// ============================================================================
// HomeHeader : en-tete de la page publique (vitrine cote client final).
// ============================================================================
// A NE PAS CONFONDRE avec Sidebar.tsx : Sidebar.tsx est le menu lateral de
// l'espace PRIVE du restaurateur (/dashboard/*), alors que HomeHeader est
// l'en-tete de la page PUBLIQUE (/), visible par n'importe quel visiteur
// avant meme de se connecter.
//
// Ce composant n'a pas besoin de "use client" car il n'utilise aucun hook
// React (pas de useState, pas de usePathname) : c'est un Server Component,
// rendu une seule fois cote serveur, ce qui est plus performant.
export default function HomeHeader() {
  return (
    // Classes Tailwind expliquees :
    // - border-b border-gray-100 : fine bordure grise en bas
    // - bg-white/80 : fond blanc a 80% d'opacite ("/80" = notation Tailwind pour l'opacite)
    // - backdrop-blur : floute ce qu'il y a derriere quand on defile (effet "verre depoli")
    // - sticky top-0 : reste colle en haut meme au defilement
    // - z-40 : place l'en-tete au-dessus des autres elements
    <header className="border-b border-gray-100 bg-white/80 backdrop-blur sticky top-0 z-40">
      {/*
        max-w-5xl mx-auto : limite la largeur et centre horizontalement.
        px-4 sm:px-6 : marge de 1rem sur mobile, 1.5rem a partir de "sm" (>=640px) — mobile-first.
        flex items-center justify-between : les 2 enfants sur une ligne, centres verticalement, ecartes au max.
      */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img
            src="/logo.svg"
            alt="Logo SaaS Reservation IA"
            className="h-9 w-9 rounded-lg object-cover"
          />
          <span className="font-bold text-primary text-lg">
            SaaS Reservation IA
          </span>
        </div>

        {/*
          Lien discret car ce n'est PAS la cible principale de cette page :
          les visiteurs veulent reserver, pas se connecter au back-office.
          <Link> de Next.js = navigation sans recharger toute la page.
        */}
        <nav className="flex items-center gap-4">
          <Link
            href="/login"
            className="text-sm font-medium text-gray-600 hover:text-primary transition"
          >
            Espace restaurateur
          </Link>
          
        </nav>
      </div>
    </header>
  );
}
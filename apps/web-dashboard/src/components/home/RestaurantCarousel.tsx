"use client";
// "use client" : ce composant charge des donnees dans le navigateur, retient
// un etat (useState) et reagit aux clics sur les fleches. La page d'accueil,
// elle, reste un Server Component.

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchRestaurants, type PublicRestaurant } from "@/lib/restaurants";

type Status = "loading" | "error" | "ready";

// ============================================================================
// RestaurantCarousel : bandeau d'images defilant avec deux fleches
// ============================================================================
// Principe :
//   - une "piste" (track) horizontale contient toutes les cartes cote a cote ;
//   - la piste deborde de son conteneur et cache sa barre de defilement ;
//   - cliquer sur une fleche fait defiler la piste d'exactement UNE carte ;
//   - le CSS "scroll-snap" aligne toujours une carte sur le bord gauche.
// Avantage : sur telephone, le visiteur peut AUSSI glisser du doigt, sans
// code supplementaire, car c'est un vrai defilement natif du navigateur.
export default function RestaurantCarousel() {
  const [restaurants, setRestaurants] = useState<PublicRestaurant[]>([]);
  const [status, setStatus] = useState<Status>("loading");
  const [canPrev, setCanPrev] = useState(false);
  const [canNext, setCanNext] = useState(false);
  const trackRef = useRef<HTMLDivElement>(null);

  // --------------------------------------------------------------------------
  // Chargement des restaurants
  // --------------------------------------------------------------------------
  const load = useCallback(async () => {
    try {
      const list = await fetchRestaurants();
      setRestaurants(list);
      setStatus("ready");
    } catch {
      // On ne remplace pas une liste deja affichee par une erreur lors d'un
      // simple rafraichissement : seul le premier chargement affiche l'erreur.
      setStatus((current) => (current === "ready" ? "ready" : "error"));
    }
  }, []);

  useEffect(() => {
    void load();
    // Quand le visiteur revient sur l'onglet (par exemple apres avoir ajoute
    // un restaurant dans le dashboard), on recharge la liste automatiquement.
    const onVisible = () => {
      if (document.visibilityState === "visible") void load();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => document.removeEventListener("visibilitychange", onVisible);
  }, [load]);

  // --------------------------------------------------------------------------
  // Etat des fleches : desactivees quand on est deja au debut ou a la fin
  // --------------------------------------------------------------------------
  const updateArrows = useCallback(() => {
    const track = trackRef.current;
    if (!track) return;
    // scrollLeft : distance deja defilee depuis la gauche.
    // clientWidth : largeur visible. scrollWidth : largeur totale du contenu.
    // Le "- 1" absorbe les arrondis de pixels de certains navigateurs.
    setCanPrev(track.scrollLeft > 1);
    setCanNext(track.scrollLeft + track.clientWidth < track.scrollWidth - 1);
  }, []);

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    updateArrows();
    // ResizeObserver : recalcule quand la largeur change (rotation du
    // telephone, fenetre redimensionnee...).
    const observer = new ResizeObserver(updateArrows);
    observer.observe(track);
    return () => observer.disconnect();
  }, [restaurants, status, updateArrows]);

  // --------------------------------------------------------------------------
  // Defilement d'une carte vers la gauche (-1) ou vers la droite (+1)
  // --------------------------------------------------------------------------
  function scrollByCard(direction: -1 | 1) {
    const track = trackRef.current;
    const firstCard = track?.firstElementChild as HTMLElement | null;
    if (!track || !firstCard) return;
    // Largeur d'une carte + espace entre deux cartes (la propriete CSS gap).
    const gap = parseFloat(getComputedStyle(track).columnGap) || 0;
    // Respecte le reglage systeme "reduire les animations".
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    track.scrollBy({
      left: direction * (firstCard.offsetWidth + gap),
      behavior: reduceMotion ? "auto" : "smooth",
    });
  }

  // Les fleches du clavier fonctionnent aussi quand le bandeau a le focus.
  function onKeyDown(event: React.KeyboardEvent) {
    if (event.key === "ArrowLeft") { event.preventDefault(); scrollByCard(-1); }
    if (event.key === "ArrowRight") { event.preventDefault(); scrollByCard(1); }
  }

  // --------------------------------------------------------------------------
  // Etats intermediaires : chargement, erreur, liste vide
  // --------------------------------------------------------------------------
  if (status === "loading") {
    return (
      <div className="flex gap-6 overflow-hidden" role="status" aria-label="Chargement des restaurants">
        {[0, 1, 2].map((i) => (
          <div key={i} className="w-[85%] sm:w-[calc(50%-0.75rem)] lg:w-[calc(33.333%-1rem)] shrink-0 aspect-[4/3] rounded-2xl bg-gray-100 animate-pulse" />
        ))}
      </div>
    );
  }
  if (status === "error") {
    return (
      <div className="rounded-2xl border border-gray-200 bg-white p-6 text-center text-gray-600" role="alert">
        Les restaurants ne peuvent pas etre charges pour le moment.
        <button type="button" onClick={() => { setStatus("loading"); void load(); }} className="ml-2 font-semibold text-primary underline">
          Reessayer
        </button>
      </div>
    );
  }
  if (restaurants.length === 0) {
    return (
      <p className="rounded-2xl border border-dashed border-gray-300 bg-white p-6 text-center text-gray-500">
        Aucun restaurant pour le moment. Revenez bientot !
      </p>
    );
  }

  // Les fleches n'apparaissent que si toutes les cartes ne tiennent pas a l'ecran.
  const showArrows = canPrev || canNext;

  return (
    <div className="relative">
      {/*
        LA PISTE :
        - flex + gap-6 : cartes alignees horizontalement, espacees de 1.5rem ;
        - overflow-x-auto : autorise le defilement horizontal ;
        - snap-x snap-mandatory : chaque defilement s'arrete pile sur une carte ;
        - [scrollbar-width:none] et [&::-webkit-scrollbar]:hidden : cachent la
          barre de defilement (Firefox, puis Chrome/Safari). Les fleches la
          remplacent.
        - onScroll : met a jour les fleches pendant le defilement (fleches,
          doigt, molette ou clavier).
      */}
      <div
        ref={trackRef}
        onScroll={updateArrows}
        onKeyDown={onKeyDown}
        tabIndex={0}
        role="region"
        aria-roledescription="carrousel"
        aria-label="Restaurants partenaires"
        className="flex gap-6 overflow-x-auto snap-x snap-mandatory scroll-smooth pb-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary rounded-2xl"
      >
        {restaurants.map((restaurant, index) => (
          // Largeur des cartes selon l'ecran (mobile-first) :
          //   mobile : 85 % -> on devine la carte suivante, invitation a defiler ;
          //   >= 640px : 2 cartes visibles ; >= 1024px : 3 cartes visibles.
          // Calcul pour 3 cartes : (100% - 2 espaces de 1.5rem) / 3 = 33.333% - 1rem.
          <article
            key={restaurant.id}
            aria-label={`${index + 1} sur ${restaurants.length} : ${restaurant.name}`}
            className="w-[85%] sm:w-[calc(50%-0.75rem)] lg:w-[calc(33.333%-1rem)] shrink-0 snap-start overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm"
          >
            {/* aspect-[4/3] : toutes les images ont la meme proportion ;
                object-cover : l'image remplit le cadre sans etre deformee. */}
            {/* eslint-disable-next-line @next/next/no-img-element -- images de sources variees (URL ou data:) */}
            <img
              src={restaurant.image_url}
              alt={`Photo du restaurant ${restaurant.name}`}
              loading="lazy"
              className="aspect-[4/3] w-full object-cover bg-gray-100"
              // Si l'image est introuvable, on affiche un fond neutre plutot
              // qu'une icone d'image cassee.
              onError={(event) => { event.currentTarget.style.visibility = "hidden"; }}
            />
            <div className="p-5">
              <h3 className="font-semibold text-gray-900">{restaurant.name}</h3>
              <p className="mt-1 text-sm text-primary">
                {[restaurant.cuisine, restaurant.city].filter(Boolean).join(" · ")}
              </p>
              {restaurant.description && (
                <p className="mt-2 text-sm text-gray-600 line-clamp-2">{restaurant.description}</p>
              )}
            </div>
          </article>
        ))}
      </div>

      {showArrows && (
        <>
          {/*
            LES FLECHES : positionnees en absolu par-dessus la piste, a gauche
            et a droite, centrees verticalement sur les images (top-[38%]).
            disabled : la fleche gauche est grisee au debut, la droite a la fin.
            aria-label : texte lu par les lecteurs d'ecran, car "‹" seul ne
            veut rien dire a l'oral.
          */}
          <ArrowButton direction="previous" disabled={!canPrev} onClick={() => scrollByCard(-1)} />
          <ArrowButton direction="next" disabled={!canNext} onClick={() => scrollByCard(1)} />
        </>
      )}
    </div>
  );
}

function ArrowButton({ direction, disabled, onClick }: {
  direction: "previous" | "next"; disabled: boolean; onClick: () => void;
}) {
  const isPrevious = direction === "previous";
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={isPrevious ? "Restaurant precedent" : "Restaurant suivant"}
      className={`absolute top-[38%] -translate-y-1/2 ${isPrevious ? "left-2 sm:-left-5" : "right-2 sm:-right-5"} flex h-11 w-11 items-center justify-center rounded-full bg-white text-primary shadow-lg ring-1 ring-gray-200 transition hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40`}
    >
      {/* Icone SVG dessinee a la main : pas besoin de librairie d'icones. */}
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d={isPrevious ? "M15 5l-7 7 7 7" : "M9 5l7 7-7 7"} stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </button>
  );
}

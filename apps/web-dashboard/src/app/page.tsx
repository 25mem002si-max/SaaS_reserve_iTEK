"use client";

import { useMemo, useState } from "react";
import Image from "next/image";
import ChatWidget from "@/components/chat/ChatWidget";
import HomeHeader from "@/components/home/HomeHeader";
import HomeFooter from "@/components/home/HomeFooter";
import RestaurantCarousel from "@/components/home/RestaurantCarousel";

// ============================================================================
// Donnees statiques de la page (restaurants + features + steps + images)
// ============================================================================
// On definit ces tableaux EN DEHORS du composant HomePage, au niveau du
// fichier, car ils ne dependent d'aucune donnee dynamique (pas de props,
// pas d'API) : les redefinir a chaque rendu serait inutile.

// Les restaurants proposes au client. C'est desormais la TOUTE PREMIERE
// decision du parcours de reservation (etape 1) : avant de discuter avec
// l'assistant, le client doit choisir OU il souhaite manger.
const restaurants = [
  {
    id: "savanna",
    name: "Savanna Table",
    cuisine: "Cuisine africaine contemporaine",
    location: "Centre-ville",
    rating: "4.8",
    image:
      "https://images.unsplash.com/photo-1515003197210-e0cd71810b5f?auto=format&fit=crop&w=1200&q=85",
  },
  {
    id: "terra",
    name: "Terra Bella",
    cuisine: "Italienne & mediterraneenne",
    location: "Quartier des affaires",
    rating: "4.7",
    image:
      "https://images.unsplash.com/photo-1513104890138-7c749659a591?auto=format&fit=crop&w=1200&q=85",
  },
  {
    id: "skyline",
    name: "Skyline Rooftop",
    cuisine: "Grillades & cuisine fusion",
    location: "Rooftop panoramique",
    rating: "4.9",
    image:
      "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1200&q=85",
  },
];

// Les 4 arguments cles affiches dans la section "Pourquoi reserver via
// notre assistant IA ?". Chaque objet a un "title" (titre court, en gras)
// et une "description" (phrase d'explication).
const features = [
  {
    title: "Disponible 24h/24 et 7j/7",
    description:
      "Notre assistant IA repond instantanement, même en dehors des heures d'ouverture du restaurant.",
  },
  {
    title: "Confirmation en moins d'une minute",
    description:
      "Plus besoin d'attendre un appel ou un message : la reservation est confirmée immediatement.",
  },
  {
    title: "Paiement Mobile Money securisé",
    description:
      "Versez votre acompte directement depuis le chat pour garantir votre table.",
  },
  {
    title: "Aucune double reservation",
    description:
      "Un systeme de verrouillage en temps reel evite qu'une meme table soit reservée deux fois.",
  },
];

// Les 4 etapes du parcours client, affichees dans la section "Comment ca
// marche". La nouvelle etape 1 ("Choisissez votre restaurant") a ete
// ajoutee avant les 3 etapes existantes, qui sont conservees a l'identique
// (juste renumerotees 2, 3, 4). Le champ "number" sert a la fois de cle
// unique React et de texte affiche dans le rond numerote.
const steps = [
  {
    number: "1",
    title: "Choisissez votre restaurant",
    description: "Parcourez nos adresses partenaires et selectionnez celle qui vous fait envie.",
  },
  {
    number: "2",
    title: "Discutez avec l'assistant",
    description: "Dites-lui la date, l'heure et le nombre de convives souhaites.",
  },
  {
    number: "3",
    title: "Choisissez votre table",
    description: "L'assistant vous propose les tables disponibles selon vos criteres.",
  },
  {
    number: "4",
    title: "Confirmez et payez l'acompte",
    description: "Recevez votre confirmation par Mobile Money, votre table est reservee.",
  },
];

const promoImages = [
  {
    src: "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80",
    alt: "Restaurant cosy",
    label: "Ambiance chic",
    type: "Restaurant",
  },
  {
    src: "https://images.unsplash.com/photo-1552566626-52f8b828add9?auto=format&fit=crop&w=900&q=80",
    alt: "Table dressée dans un restaurant",
    label: "Cuisine du jour",
    type: "Plat",
  },
  {
    src: "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=900&q=80",
    alt: "Plat gastronomique",
    label: "Assiette gourmande",
    type: "Plat",
  },
  {
    src: "https://images.unsplash.com/photo-1528605248644-14dd04022da1?auto=format&fit=crop&w=900&q=80",
    alt: "Restaurant avec clients",
    label: "Moment partagé",
    type: "Restaurant",
  },
  {
    src: "https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=900&q=80",
    alt: "Plat préparé",
    label: "Signature chef",
    type: "Plat",
  },
  {
    src: "https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=900&q=80",
    alt: "Restaurant élégant de nuit",
    label: "Soirée premium",
    type: "Restaurant",
  },
];

// ============================================================================
// HomePage : page vitrine publique du restaurant.
// ============================================================================
// C'est la page d'accueil "CLIENTE" (route "/"), a ne pas confondre avec
// "/dashboard" qui est l'accueil du RESTAURATEUR (back-office prive).
//
// Structure de haut en bas (comme un entonnoir de conversion classique) :
//   1. HomeHeader          -> en-tete avec nom du produit + lien connexion
//   2. Section HEROS       -> gros visuel + argument principal + CTA
//   3. Section RESTAURANT  -> etape 1 : choisir OU manger (NOUVEAU)
//   4. Section ARGUMENTS   -> 4 raisons de faire confiance au service
//   5. Section ETAPES      -> comment fonctionne la reservation, en 4 etapes
//   6. Section PUB         -> bandeau photos en defilement
//   7. Section CHAT        -> l'objectif final : le widget de chat lui-meme
//   8. HomeFooter          -> pied de page avec mentions legales
//
// Le composant est marque "use client" car il gere desormais deux etats
// locaux : le restaurant selectionne par le client, et l'image agrandie
// dans le bandeau promotionnel.
export default function HomePage() {
  const [zoomedImage, setZoomedImage] = useState<string | null>(null);

  // Restaurant choisi par le client. On initialise avec le premier de la
  // liste pour que la section "Reservez maintenant" affiche toujours un
  // recapitulatif coherent, meme si le client n'a pas encore clique.
  const [selectedRestaurant, setSelectedRestaurant] = useState(restaurants[0].id);

  const currentRestaurant = useMemo(
    () => restaurants.find((restaurant) => restaurant.id === selectedRestaurant) ?? restaurants[0],
    [selectedRestaurant],
  );

  return (
    // <main> : balise HTML semantique pour le contenu principal de la page.
    <main className="min-h-screen flex flex-col bg-white">
      <HomeHeader />

      {/* ================= SECTION 1 : HEROS ================= */}
      {/*
        Le heros a maintenant une VRAIE photo de restaurant en arriere-plan
        (et non plus un simple degrade uni) : c'est ce qui rend la page
        immediatement plus chaleureuse et "vendeuse". Le degrade sombre est
        conserve PAR-DESSUS la photo (en superposition), uniquement pour
        garantir que le texte blanc reste parfaitement lisible.
      */}
      <section className="relative isolate overflow-hidden bg-primary text-white">
        <div className="absolute inset-0 -z-20">
          <Image
            src="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=2200&q=90"
            alt="Salle de restaurant chaleureuse et conviviale"
            fill
            priority
            sizes="100vw"
            className="object-cover opacity-40"
          />
          <div className="absolute inset-0 bg-gradient-to-br from-primary/95 via-primary/85 to-primary-light/70" />
        </div>

        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 py-16 sm:py-28 text-center">
          <p className="inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.18em] text-white/90 backdrop-blur-sm">
            <span className="h-2 w-2 rounded-full bg-accent" />
            Votre table, sans attente
          </p>

          <h1 className="mt-5 text-3xl sm:text-5xl font-bold leading-tight">
            Reservez votre table
            <br className="hidden sm:block" /> en quelques secondes
          </h1>

          <p className="mt-4 text-base sm:text-lg text-white/85 max-w-2xl mx-auto">
            Choisissez votre restaurant, discutez avec notre assistant IA et
            confirmez votre reservation sans appel telephonique et sans attente.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <a
              href="#choisir-restaurant"
              className="inline-flex items-center justify-center bg-accent text-primary font-semibold px-6 py-3 rounded-full shadow-lg hover:brightness-95 transition"
            >
              Choisir un restaurant
            </a>
            <a
              href="#reserver"
              className="inline-flex items-center justify-center bg-white/10 border border-white/30 text-white font-semibold px-6 py-3 rounded-full backdrop-blur-sm hover:bg-white/20 transition"
            >
              Discuter avec l&apos;assistant
            </a>
          </div>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-white/80">
            <span className="inline-flex items-center gap-2">
              <span className="text-accent">★</span> Reservation en 4 etapes
            </span>
            <span className="inline-flex items-center gap-2">
              <span className="text-accent">★</span> Reponse instantanee
            </span>
            <span className="inline-flex items-center gap-2">
              <span className="text-accent">★</span> Restaurants selectionnes
            </span>
          </div>
        </div>
      </section>

      {/* ================= SECTION 2 : CHOIX DU RESTAURANT (ETAPE 1) ================= */}
      {/*
        Nouvelle section : c'est ici que se joue la toute PREMIERE etape du
        parcours. Le client parcourt des cartes illustrees (photo, nom,
        cuisine, quartier) et clique pour choisir son restaurant. La carte
        selectionnee est mise en evidence par un anneau "accent" et une
        coche, afin que le choix soit sans ambiguite.
        id="choisir-restaurant" est la cible de l'ancre du bouton du heros.
      */}

      <section className="bg-gray-50 py-14 sm:py-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
            <h2 className="text-2xl sm:text-3xl font-bold text-center text-gray-900">
              Nos restaurants partenaires
            </h2>
            <p className="mt-2 mb-10 text-center text-gray-600">
                Parcourez les restaurants, puis reservez via l&apos;assistant.
            </p>
          <RestaurantCarousel />
        </div>
      </section>

      <section id="choisir-restaurant" className="bg-gray-50 py-14 sm:py-20 scroll-mt-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="text-center max-w-2xl mx-auto">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">
              Etape 1
            </p>
            <h2 className="mt-2 text-2xl sm:text-3xl font-bold text-gray-900">
              Ou souhaitez-vous manger ?
            </h2>
            <p className="mt-2 text-gray-600">
              Choisissez d&apos;abord votre restaurant : votre selection sera
              rappelee a l&apos;assistant lors de la reservation.
            </p>
          </div>

          <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-6">
            {restaurants.map((restaurant) => {
              const isSelected = restaurant.id === selectedRestaurant;
              return (
                <button
                  key={restaurant.id}
                  type="button"
                  onClick={() => setSelectedRestaurant(restaurant.id)}
                  aria-pressed={isSelected}
                  className={`group text-left overflow-hidden rounded-2xl border bg-white shadow-sm transition ${
                    isSelected
                      ? "border-accent ring-4 ring-accent/20 shadow-lg"
                      : "border-gray-100 hover:-translate-y-1 hover:shadow-xl"
                  }`}
                >
                  <div className="relative h-44 overflow-hidden">
                    <Image
                      src={restaurant.image}
                      alt={restaurant.name}
                      fill
                      sizes="(max-width: 640px) 100vw, 33vw"
                      className="object-cover transition duration-500 group-hover:scale-105"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/0 to-black/0" />
                    <span className="absolute top-3 right-3 inline-flex items-center gap-1 rounded-full bg-white/90 px-2.5 py-1 text-xs font-semibold text-gray-900">
                      ★ {restaurant.rating}
                    </span>
                    {isSelected && (
                      <span className="absolute top-3 left-3 grid h-7 w-7 place-items-center rounded-full bg-accent text-primary font-bold shadow">
                        ✓
                      </span>
                    )}
                  </div>
                  <div className="p-5">
                    <h3 className="font-semibold text-gray-900">{restaurant.name}</h3>
                    <p className="mt-1 text-sm text-gray-600">{restaurant.cuisine}</p>
                    <p className="mt-2 text-xs font-medium text-primary">
                      📍 {restaurant.location}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3 text-center">
            <p className="text-sm text-gray-600">
              Restaurant choisi :{" "}
              <span className="font-semibold text-gray-900">{currentRestaurant.name}</span>
            </p>
            <a
              href="#reserver"
              className="inline-flex items-center justify-center bg-primary text-white font-semibold px-6 py-2.5 rounded-full shadow hover:bg-primary-light transition"
            >
              Continuer avec l&apos;assistant →
            </a>
          </div>
        </div>
      </section>

      {/* ================= SECTION 3 : ARGUMENTS CLES ================= */}
      <section className="bg-white py-14 sm:py-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-center text-gray-900">
            Pourquoi reserver via notre assistant IA ?
          </h2>

          <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 gap-6">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="rounded-2xl border border-gray-100 bg-gray-50 p-6 hover:shadow-md transition"
              >
                <div className="w-9 h-9 rounded-full bg-accent/15 text-accent flex items-center justify-center font-bold">
                  ✓
                </div>
                <h3 className="mt-4 font-semibold text-gray-900">
                  {feature.title}
                </h3>
                <p className="mt-1 text-sm text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= SECTION 4 : COMMENT CA MARCHE ================= */}
      {/* bg-gray-50 : fond gris tres clair, pour alterner visuellement avec
          la section blanche precedente et la section blanche suivante. */}
      <section id="comment-ca-marche" className="bg-gray-50 py-14 sm:py-20 scroll-mt-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl sm:text-3xl font-bold text-center text-gray-900">
            Comment ca marche
          </h2>
          <p className="mt-2 text-center text-gray-600 max-w-2xl mx-auto">
            4 etapes simples, du choix du restaurant jusqu&apos;a la confirmation de votre table.
          </p>

          {/*
            grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 : 1 colonne sur
            mobile, 2 colonnes sur tablette, 4 colonnes cote a cote sur
            grand ecran (les 4 etapes visibles d'un coup).
          */}
          <div className="mt-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step) => (
              <div key={step.number} className="text-center">
                <div className="w-12 h-12 mx-auto rounded-full bg-primary text-white flex items-center justify-center text-lg font-bold">
                  {step.number}
                </div>
                <h3 className="mt-4 font-semibold text-gray-900">
                  {step.title}
                </h3>
                <p className="mt-1 text-sm text-gray-600">
                  {step.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ================= SECTION 5 : BLOC PUBLICITAIRE ================= */}
      <section className="bg-gradient-to-r from-primary via-primary to-primary-light py-14 sm:py-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="rounded-3xl border border-white/20 bg-white/10 p-8 shadow-xl backdrop-blur-sm sm:p-10">
            <div className="grid items-center gap-8 lg:grid-cols-[1.3fr_1fr]">
              <div className="text-white">
                <p className="inline-flex rounded-full bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-white/90">
                  Offre spéciale
                </p>
                <h2 className="mt-4 text-2xl sm:text-4xl font-bold leading-tight">
                  Profitez d&apos;une réservation simplifiée,
                  <br className="hidden sm:block" /> sans attente ni stress.
                </h2>
                <p className="mt-4 max-w-xl text-base text-white/85 sm:text-lg">
                  Notre assistant IA vous aide à choisir un restaurant, une table, vérifier la
                  disponibilité et confirmer votre réservation en quelques secondes,
                  partout et à tout moment.
                </p>

                <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                  <a
                    href="#choisir-restaurant"
                    className="inline-flex items-center justify-center rounded-full bg-white px-6 py-3 font-semibold text-primary transition hover:bg-gray-50"
                  >
                    Réserver maintenant
                  </a>
                  <a
                    href="#comment-ca-marche"
                    className="inline-flex items-center justify-center rounded-full border border-white/40 bg-white/5 px-6 py-3 font-semibold text-white transition hover:bg-white/10"
                  >
                    Voir le parcours
                  </a>
                </div>
              </div>

              <div className="rounded-3xl border border-white/20 bg-white/5 p-3">
                <div className="mb-3 flex items-center justify-between px-2">
                  <p className="text-sm font-medium text-white/80">
                    Restaurants &amp; plats
                  </p>
                  <span className="rounded-full border border-white/20 bg-white/5 px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-white/70">
                    En direct
                  </span>
                </div>

                <div className="overflow-hidden rounded-2xl">
                  <div className="marquee-track">
                    {[...promoImages, ...promoImages].map((image, index) => {
                      const isZoomed = zoomedImage === image.alt;

                      return (
                        <button
                          key={`${image.alt}-${index}`}
                          type="button"
                          onClick={() => setZoomedImage(isZoomed ? null : image.alt)}
                          className="marquee-item w-[220px] shrink-0 rounded-2xl border border-white/15 bg-white/5 p-2 text-left transition hover:border-white/30"
                          aria-pressed={isZoomed}
                        >
                          <div className="relative h-40 overflow-hidden rounded-xl">
                            <Image
                              src={image.src}
                              alt={image.alt}
                              fill
                              sizes="220px"
                              className={`promo-image object-cover ${isZoomed ? "promo-image-zoomed" : ""}`}
                            />
                          </div>
                          <div className="mt-2 flex items-center justify-between gap-2">
                            <span className="text-sm font-semibold text-white truncate">
                              {image.label}
                            </span>
                            <span className="text-[10px] uppercase tracking-[0.2em] text-white/60">
                              {image.type}
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ================= SECTION 6 : WIDGET DE CHAT ================= */}
      {/*
        Cette section est l'OBJECTIF FINAL de toute la page : c'est ici que
        le visiteur reserve reellement sa table, via le composant
        <ChatWidget /> deja existant (non modifie). Elle rappelle desormais
        le restaurant choisi a l'etape 1, pour que le client garde le
        contexte visuel jusqu'au bout du parcours.
        id="reserver" : cible des ancres "#reserver" plus haut sur la page.
        scroll-mt-20 : evite que le titre se retrouve cache sous HomeHeader
        (qui est "sticky") apres le defilement automatique.
      */}
      <section id="reserver" className="bg-white py-14 sm:py-20 scroll-mt-20">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Reservez maintenant
          </h2>
          <p className="mt-2 text-gray-600">
            Notre assistant est en ligne et pret a vous aider.
          </p>

          {/* Recapitulatif du restaurant choisi a l'etape 1 : cela evite
              que le client oublie son choix en arrivant sur le chat, et
              permet de le communiquer facilement a l'assistant. */}
          <div className="mt-6 inline-flex items-center gap-3 rounded-full border border-gray-200 bg-gray-50 px-4 py-2 text-left">
            <div className="relative h-9 w-9 overflow-hidden rounded-full shrink-0">
              <Image
                src={currentRestaurant.image}
                alt={currentRestaurant.name}
                fill
                sizes="36px"
                className="object-cover"
              />
            </div>
            <span className="text-sm text-gray-700">
              Restaurant choisi :{" "}
              <span className="font-semibold text-gray-900">{currentRestaurant.name}</span>
            </span>
            <a href="#choisir-restaurant" className="text-xs font-semibold text-primary hover:underline">
              Changer
            </a>
          </div>

          {/* Le composant ChatWidget existant (connecte au backend via
              WebSocket) est simplement re-encadre dans cette nouvelle
              section visuelle — sa logique interne n'est pas modifiee. */}
          <div className="mt-8">
            <ChatWidget />
          </div>
        </div>
      </section>

      <HomeFooter />
    </main>
  );
}

import clsx from "clsx";
import type { RestaurantTable } from "@/lib/types";

// clsx est une petite librairie utilitaire qui permet de combiner des
// classes Tailwind de façon conditionnelle, sans avoir à écrire des
// concatenations de chaines de caracteres a la main (`"a " + (x ? "b" : "")`).

// Dictionnaire qui associe chaque statut possible d'une table (defini dans
// RestaurantTable, voir src/lib/types.ts) a un jeu de classes Tailwind.
// C'est ce qui donne la couleur visuelle : vert = libre, orange = reservee,
// rouge = occupee, gris = verrouillee (lock Redis pose par le backend).
const statusColor: Record<string, string> = {
  FREE: "bg-success/10 border-success text-success",
  RESERVED: "bg-accent/10 border-accent text-accent",
  OCCUPIED: "bg-danger/10 border-danger text-danger",
  LOCKED: "bg-gray-200 border-gray-400 text-gray-600",
};

// TableCard = une "carte" cliquable representant UNE table du restaurant.
// Elle est purement "presentationnelle" : elle ne va pas chercher les
// donnees elle-meme, elle se contente d'afficher ce qu'on lui donne en props
// et de remonter l'evenement de clic au parent (FloorPlan) via `onClick`.
//
// props:
// - table   : l'objet table a afficher (obligatoire)
// - onClick : fonction optionnelle appelee avec la table quand on clique
//             dessus. C'est FloorPlan qui va s'en servir pour savoir quelle
//             table ouvrir dans la modale.
export default function TableCard({
  table,
  onClick,
}: {
  table: RestaurantTable;
  onClick?: (table: RestaurantTable) => void;
}) {
  // On recupere les classes de couleur correspondant au statut de la table.
  // Le `?? statusColor.FREE` est une securite : si jamais le backend envoie
  // un statut inconnu/inattendu, on retombe sur le style "libre" au lieu de
  // planter ou d'afficher une carte sans style.
  const color = statusColor[table.status] ?? statusColor.FREE;

  return (
    // On utilise un <button> (et non une simple <div>) pour deux raisons :
    // 1. Semantique HTML correcte : un element cliquable doit etre un bouton.
    // 2. Accessibilite gratuite : navigable au clavier (Tab + Entree),
    //    lu correctement par les lecteurs d'ecran.
    <button
      type="button"
      // onClick?.(table) = "si onClick est defini, on l'appelle avec la table
      // courante". Le `?.` (optional chaining) evite un crash si le parent
      // n'a pas fourni de onClick (ex: si on reutilise TableCard ailleurs
      // en mode "affichage seul").
      onClick={() => onClick?.(table)}
      className={clsx(
        // Style de base commun a toutes les tables, quel que soit leur statut
        "rounded-xl border p-3 text-center transition hover:shadow-md hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-primary",
        // Puis on ajoute les classes de couleur specifiques au statut
        color
      )}
    >
      <p className="font-semibold">Table {table.number_label}</p>
      <p className="text-xs">{table.capacity} places - {table.zone}</p>
      <p className="text-xs mt-1 font-medium">{table.status}</p>
    </button>
  );
}
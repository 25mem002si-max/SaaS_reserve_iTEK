"use client";

import { PERIOD_OPTIONS, type AnalyticsPeriod } from "@/lib/analytics";

// ============================================================================
// PeriodFilter : selecteur de la fenetre temporelle des graphiques Analytics.
// ============================================================================
// On choisit un "segmented control" (groupe de boutons cote a cote, un
// seul actif a la fois) plutot qu'un <select> HTML classique : avec
// seulement 3 options fixes, les boutons sont plus rapides a utiliser au
// doigt sur mobile (pas besoin d'ouvrir un menu deroulant) — coherent avec
// l'exigence mobile-first du cahier des charges.
//
// Ce composant est volontairement "controle" (comme un <input> React
// classique) : il ne possede AUCUN etat interne, il se contente de
// recevoir `value` (la periode active) et d'appeler `onChange` au clic. La
// gestion reelle de l'etat vit dans le composant parent (la page
// Analytics), ce qui permet a CE MEME etat d'etre partage par les 3
// graphiques sans dupliquer la logique de filtre dans chacun d'eux.
interface PeriodFilterProps {
  /** Periode actuellement selectionnee. */
  value: AnalyticsPeriod;
  /** Appele avec la nouvelle periode des qu'un bouton est clique. */
  onChange: (period: AnalyticsPeriod) => void;
}

export default function PeriodFilter({ value, onChange }: PeriodFilterProps) {
  return (
    // `role="group"` + `aria-label` : indique aux technologies
    // d'assistance que ces boutons forment un ensemble logique (un
    // filtre), et non une liste d'actions independantes.
    <div
      role="group"
      aria-label="Filtrer les graphiques par periode"
      className="inline-flex rounded-full border bg-white p-1 text-sm shadow-sm"
    >
      {PERIOD_OPTIONS.map((option) => {
        const isActive = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            // `aria-pressed` : signale aux lecteurs d'ecran qu'il s'agit
            // d'un bouton "bascule" (toggle) et communique son etat
            // actif/inactif, en plus du style visuel ci-dessous.
            aria-pressed={isActive}
            className={`px-3 py-1.5 rounded-full font-medium transition ${
              isActive
                ? "bg-primary text-white"
                : "text-gray-600 hover:bg-gray-100"
            }`}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

// ============================================================================
// Constantes et types lies au FILTRE DE PERIODE de la page Analytics.
// ============================================================================
// Isole dans son propre fichier (plutot que dans lib/types.ts, qui ne
// contient que les entites alignees sur le schema PostgreSQL comme
// Restaurant/Table/Reservation) car ce n'est pas une donnee metier stockee
// en base : c'est un simple parametre d'affichage cote frontend, partage
// entre la page Analytics, le composant PeriodFilter et les 3 graphiques.

// Les 3 fenetres temporelles proposees a l'utilisateur. On reste
// volontairement sur un type union de chaines litterales (et non un enum
// TypeScript classique) : plus simple a serialiser tel quel dans une URL
// de requete API (`?period=30d`), et suffisant pour 3 valeurs fixes.
export type AnalyticsPeriod = "7d" | "30d" | "90d";

// Periode utilisee par defaut a l'ouverture de la page, avant toute
// interaction de l'utilisateur avec le filtre.
export const DEFAULT_ANALYTICS_PERIOD: AnalyticsPeriod = "7d";

// Forme d'une option affichee dans le selecteur de periode (PeriodFilter).
interface PeriodOption {
  value: AnalyticsPeriod;
  /** Libelle court affiche SUR le bouton (ex: "7 jours"). */
  label: string;
}

// Liste ordonnee des options du filtre, utilisee par PeriodFilter pour
// generer ses boutons via `.map()` plutot que de les ecrire 3 fois a la
// main dans le JSX — si on ajoute une 4e periode plus tard (ex: "12
// mois"), il suffit d'ajouter une ligne ici.
export const PERIOD_OPTIONS: PeriodOption[] = [
  { value: "7d", label: "7 jours" },
  { value: "30d", label: "30 jours" },
  { value: "90d", label: "90 jours" },
];

// Libelle LONG associe a chaque periode (ex: "7 derniers jours"), utilise
// dans les titres des graphiques pour rappeler clairement quelle fenetre
// temporelle est affichee (ex: "Frequentation (7 derniers jours)").
// `Record<AnalyticsPeriod, string>` garantit, a la compilation, qu'on ne
// peut pas oublier de libelle pour l'une des 3 periodes definies ci-dessus.
export const PERIOD_LABELS: Record<AnalyticsPeriod, string> = {
  "7d": "7 derniers jours",
  "30d": "30 derniers jours",
  "90d": "90 derniers jours",
};

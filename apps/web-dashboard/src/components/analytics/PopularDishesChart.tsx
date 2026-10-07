"use client";

import { useMemo } from "react";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from "recharts";
import { fetchPopularDishes } from "@/lib/api";
import { useAnalyticsData } from "@/hooks/useAnalyticsData";
import { PERIOD_LABELS, type AnalyticsPeriod } from "@/lib/analytics";
import ChartCard from "./ChartCard";

// Palette reprise du design system (voir tailwind.config.ts) : on aurait
// pu utiliser directement les classes Tailwind, mais Recharts dessine le
// graphique en SVG et attend des couleurs CSS explicites (hex/rgb), pas
// des noms de classes — d'ou cette duplication volontaire des couleurs ici.
const COLORS = ["#1E3A8A", "#3B82F6", "#F59E0B", "#16A34A", "#DC2626"];

// Forme d'un plat renvoye par l'API. On declare ce type explicitement
// (plutot que de le deriver via `typeof data`) pour eviter que TypeScript
// ne melange le type `null` (etat initial du hook) avec le type des
// elements du tableau dans les valeurs par defaut ci-dessous.
interface Dish {
  name: string;
  value: number;
}

// ============================================================================
// PopularDishesChart : repartition des commandes par plat.
// ============================================================================
// Amelioration "statistiquement parlante" par rapport a la version
// d'origine : un camembert (pie chart) brut avec juste des couleurs et une
// legende ne dit pas VRAIMENT quelle part chaque plat represente. On
// calcule donc ici le TOTAL des commandes tous plats confondus, ce qui
// permet :
//   1. de trier les plats du plus au moins populaire (plus facile a lire
//      qu'un ordre arbitraire renvoye par l'API) ;
//   2. d'afficher un POURCENTAGE (et pas juste un nombre brut) sur chaque
//      part du camembert et dans l'infobulle ;
//   3. de mettre en avant le plat n°1 dans un badge dedie.

interface PopularDishesChartProps {
  period: AnalyticsPeriod;
}

export default function PopularDishesChart({ period }: PopularDishesChartProps) {
  // `[period]` en dependance : un changement de periode dans le filtre
  // partage declenche un nouvel appel a `fetchPopularDishes` avec la
  // valeur a jour (voir useAnalyticsData.ts pour le detail du mecanisme).
  const { data, isLoading, error } = useAnalyticsData(
    () => fetchPopularDishes(period),
    [period]
  );

  // On derive 3 choses a partir des donnees brutes :
  // - `sorted`  : les plats tries du plus au moins commande ;
  // - `total`   : la somme de toutes les commandes (denominateur des %) ;
  // - `top`     : le plat le plus populaire (premier element une fois trie).
  const { sorted, total, top } = useMemo<{ sorted: Dish[]; total: number; top: Dish | null }>(() => {
    if (!data || data.length === 0) {
      return { sorted: [], total: 0, top: null };
    }

    // `[...data]` : on copie le tableau avant de le trier, car `.sort()`
    // modifie le tableau EN PLACE — sans cette copie, on modifierait
    // directement l'etat `data` renvoye par le hook, ce qui est une
    // mauvaise pratique en React (l'etat doit rester immuable).
    const sortedData = [...data].sort((a, b) => b.value - a.value);
    const totalValue = sortedData.reduce((sum, dish) => sum + dish.value, 0);

    return { sorted: sortedData, total: totalValue, top: sortedData[0] };
  }, [data]);

  // Petite fonction utilitaire locale : calcule un pourcentage arrondi a
  // partir d'une valeur brute et du total. Definie ici (et pas dans
  // lib/utils.ts) car elle est tres specifique a ce composant (division
  // par `total`, qui n'a de sens que dans ce contexte).
  const toPercent = (value: number) => (total > 0 ? (value / total) * 100 : 0);

  return (
    <ChartCard
      title={`Plats populaires (${PERIOD_LABELS[period]})`}
      isLoading={isLoading}
      error={error}
      isEmpty={sorted.length === 0}
      headerExtra={
        top && (
          <span className="text-xs bg-accent/10 text-accent font-medium px-2 py-1 rounded-full">
            🏆 {top.name} — {toPercent(top.value).toFixed(0)}% des commandes
          </span>
        )
      }
    >
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={sorted}
            dataKey="value"
            nameKey="name"
            outerRadius={90}
            // `label` : fonction appelee par Recharts pour CHAQUE part du
            // camembert, afin de generer le texte affiche a cote. On y
            // calcule le pourcentage a la volee plutot que d'attendre que
            // l'API le fournisse deja calcule — ca reste juste meme si
            // l'API renvoie des comptages bruts (ex: "12 commandes") au
            // lieu de pourcentages.
            label={({ name, value }: { name: string; value: number }) =>
              `${name} (${toPercent(value).toFixed(0)}%)`
            }
          >
            {sorted.map((_, index) => (
              // `index` comme `key` est generalement deconseille en React
              // (probleme si la liste est reordonnee dynamiquement), mais
              // ici `sorted` est entierement recalcule a chaque nouvelle
              // reponse API (pas de reordonnancement partiel), donc c'est
              // sans risque.
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number, name: string) => [
              `${value} commandes (${toPercent(value).toFixed(1)}%)`,
              name,
            ]}
          />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

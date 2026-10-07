"use client";

import { useState } from "react";
import AttendanceChart from "@/components/analytics/AttendanceChart";
import PopularDishesChart from "@/components/analytics/PopularDishesChart";
import RevenueForecastChart from "@/components/analytics/RevenueForecastChart";
import PeriodFilter from "@/components/analytics/PeriodFilter";
import { DEFAULT_ANALYTICS_PERIOD, type AnalyticsPeriod } from "@/lib/analytics";

// ============================================================================
// Page Analytics : vue d'ensemble statistique du restaurant.
// ============================================================================
// Cette page etait auparavant un Server Component (pas de "use client")
// puisqu'elle ne faisait QUE de la mise en page statique. L'ajout du
// filtre de periode change ca : la page doit maintenant memoriser QUELLE
// periode est selectionnee (etat React, `useState`) et la transmettre aux
// 3 graphiques ET au composant PeriodFilter — or `useState` n'existe que
// cote client. D'ou le passage en "use client" ici.
//
// Pourquoi centraliser `period` DANS la page plutot que dans chaque
// graphique individuellement ? Parce que le filtre doit rester
// SYNCHRONISE entre les 3 graphiques : quand on choisit "30 jours", les 3
// doivent se mettre a jour ensemble, pas seulement celui sur lequel on
// clique. En React, la solution standard pour partager un etat entre
// plusieurs composants "freres" est de le faire "remonter" (lift state up)
// dans leur plus proche ancetre commun — ici, cette page — puis de le
// redescendre en props a chacun.
export default function AnalyticsPage() {
  const [period, setPeriod] = useState<AnalyticsPeriod>(DEFAULT_ANALYTICS_PERIOD);

  return (
    <div className="space-y-6">
      {/* `flex-wrap` : sur mobile, le filtre passe sous le titre plutot que
          de comprimer le texte ou deborder de l'ecran (mobile-first). */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl font-semibold">Analytics</h1>
          <p className="text-sm text-gray-500 mt-1">
            Vue d&apos;ensemble de la frequentation, des plats les plus commandes et
            des previsions de chiffre d&apos;affaires du restaurant.
          </p>
        </div>

        {/* PeriodFilter est un composant "controle" : il ne fait que
            refleter `period` et remonter les clics via `onChange`, toute
            la logique d'etat reste ici. */}
        <PeriodFilter value={period} onChange={setPeriod} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chaque graphique recoit la MEME valeur `period` : c'est ce qui
            garantit que les 3 restent synchronises entre eux. */}
        <AttendanceChart period={period} />
        <PopularDishesChart period={period} />
      </div>

      <RevenueForecastChart period={period} />
    </div>
  );
}
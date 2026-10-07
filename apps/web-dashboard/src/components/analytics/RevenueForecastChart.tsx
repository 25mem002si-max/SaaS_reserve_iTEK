"use client";

import { useMemo } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import { fetchRevenueForecast } from "@/lib/api";
import { useAnalyticsData } from "@/hooks/useAnalyticsData";
import { formatCurrency } from "@/lib/utils";
import { PERIOD_LABELS, type AnalyticsPeriod } from "@/lib/analytics";
import ChartCard from "./ChartCard";

// Formateur "compact" pour l'axe vertical (ex: "1,2 k" au lieu de
// "1200.00 $"). On veut des graduations courtes sur l'axe (sinon elles se
// chevauchent sur mobile), mais on garde le montant COMPLET et bien
// formate en devise dans l'infobulle (Tooltip) et le total ci-dessous, la
// ou la precision compte vraiment.
const compactNumberFormatter = new Intl.NumberFormat("fr-FR", {
  notation: "compact",
  compactDisplay: "short",
});

// ============================================================================
// RevenueForecastChart : prevision de chiffre d'affaires mois par mois.
// ============================================================================
// Amelioration "statistiquement parlante" : le graphique d'origine tracait
// une simple ligne, sans aucune indication de TENDANCE ni de contexte
// monetaire (les valeurs brutes ne disaient pas si c'etait des dollars,
// des francs congolais, ni si la tendance etait bonne ou mauvaise). On
// calcule ici :
//   - le TOTAL prevu sur toute la periode affichee ;
//   - le TAUX DE CROISSANCE entre le premier et le dernier mois, qui
//     resume en un seul chiffre si la tendance est a la hausse ou a la
//     baisse ;
// et on formate systematiquement les montants avec `formatCurrency` (voir
// src/lib/utils.ts) plutot que d'afficher des nombres bruts.
//
// NB : `formatCurrency` utilise USD par defaut. Le schema de donnees
// (`Restaurant.currency`) prevoit aussi le franc congolais (CDF) —
// lorsque le contexte restaurant (via useAuth ou un futur store de
// parametres) sera branche sur ce composant, il suffira de recuperer
// `restaurant.currency` et de le passer a `formatCurrency(valeur, currency)`
// a la place du defaut. On laisse ce point en TODO explicite pour ne pas
// deviner une valeur qui n'est pas encore disponible ici.
interface RevenueForecastChartProps {
  period: AnalyticsPeriod;
}

export default function RevenueForecastChart({ period }: RevenueForecastChartProps) {
  // Meme mecanisme que les 2 autres graphiques : `[period]` en dependance
  // pour recharger la prevision des que le filtre partage change.
  const { data, isLoading, error } = useAnalyticsData(
    () => fetchRevenueForecast(period),
    [period]
  );

  const stats = useMemo(() => {
    // Il faut au moins 2 points pour qu'un "taux de croissance" ait un
    // sens (comparer un mois a lui-meme ne veut rien dire).
    if (!data || data.length < 2) return null;

    const first = data[0].revenue;
    const last = data[data.length - 1].revenue;
    const total = data.reduce((sum, month) => sum + month.revenue, 0);

    // Taux de croissance global sur la periode = variation relative entre
    // le premier et le dernier mois affiche, exprimee en pourcentage.
    // Protection contre une division par zero si le premier mois est a 0
    // (cas limite mais possible pour un nouveau restaurant sans historique).
    const growthRate = first !== 0 ? ((last - first) / first) * 100 : 0;

    return { total, growthRate, isPositive: growthRate >= 0 };
  }, [data]);

  return (
    <ChartCard
      title={`Prevision de chiffre d'affaires — periode : ${PERIOD_LABELS[period]}`}
      isLoading={isLoading}
      error={error}
      isEmpty={!data || data.length === 0}
      headerExtra={
        stats && (
          // Badge colore vert/rouge selon le sens de la tendance : un code
          // couleur universellement compris (vert = bon signe, rouge =
          // signal d'alerte), plus rapide a interpreter qu'un simple chiffre.
          <span
            className={`text-xs font-medium px-2 py-1 rounded-full ${
              stats.isPositive ? "bg-success/10 text-success" : "bg-danger/10 text-danger"
            }`}
          >
            {stats.isPositive ? "▲" : "▼"} {Math.abs(stats.growthRate).toFixed(1)}% sur la periode
          </span>
        )
      }
    >
      <ResponsiveContainer width="100%" height={260}>
        <AreaChart data={data ?? []}>
          {/* `<defs>` + `linearGradient` : on definit un degrade SVG
              reutilisable (opaque en haut, transparent en bas), applique
              ensuite a la zone sous la courbe via `fill="url(#revenueGradient)"`
              sur le composant <Area>. C'est ce degrade qui donne un rendu
              "professionnel" a la courbe plutot qu'un simple trait plein. */}
          <defs>
            <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#16A34A" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#16A34A" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="month" tick={{ fontSize: 12 }} />
          <YAxis
            tick={{ fontSize: 12 }}
            width={56}
            tickFormatter={(value: number) => compactNumberFormatter.format(value)}
          />
          {/* L'infobulle, elle, affiche le montant COMPLET et correctement
              formate en devise (ex: "1 200,00 $") — c'est la que la
              precision compte, contrairement a l'axe qui ne sert qu'a
              donner un ordre de grandeur. */}
          <Tooltip formatter={(value: number) => [formatCurrency(value), "Chiffre d'affaires"]} />
          <Area
            type="monotone"
            dataKey="revenue"
            stroke="#16A34A"
            strokeWidth={2}
            fill="url(#revenueGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>

      {stats && (
        <p className="text-xs text-gray-400 mt-2">
          Total previsionnel sur la periode :{" "}
          <strong className="text-gray-600">{formatCurrency(stats.total)}</strong>
        </p>
      )}
    </ChartCard>
  );
}

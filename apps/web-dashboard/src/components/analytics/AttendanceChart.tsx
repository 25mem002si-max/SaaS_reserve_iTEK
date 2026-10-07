"use client";

import { useMemo } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
  Label,
} from "recharts";
import { fetchAttendanceStats } from "@/lib/api";
import { useAnalyticsData } from "@/hooks/useAnalyticsData";
import { PERIOD_LABELS, type AnalyticsPeriod } from "@/lib/analytics";
import ChartCard from "./ChartCard";

// ============================================================================
// AttendanceChart : frequentation (nombre de convives) sur la periode choisie.
// ============================================================================
// Depuis l'ajout du filtre de periode (PeriodFilter, pilote par la page
// Analytics), la fenetre temporelle n'est plus fixee a "7 derniers jours"
// en dur : elle vient de la prop `period` (voir plus bas) et peut valoir
// 7, 30 ou 90 jours selon le choix de l'utilisateur.
// Objectif "statistiquement parlant" : un simple diagramme en barres ne dit
// pas grand-chose au restaurateur tant qu'il n'a pas de point de
// comparaison. On calcule donc ici, cote client, 3 indicateurs derives des
// memes donnees brutes renvoyees par l'API :
//   - le TOTAL de convives sur la periode ;
//   - la MOYENNE par jour (utilisee aussi pour tracer une ligne de
//     reference sur le graphique) ;
//   - le MEILLEUR jour (celui avec le plus de convives).
// On ne demande PAS ces calculs au backend : ce sont de simples agregations
// sur un tableau deja petit (7 valeurs), donc les faire cote client evite
// un aller-retour reseau supplementaire et garde le backend simple.

// `period` est fourni par la page Analytics (parent), qui possede l'etat
// partage du filtre — ce composant n'a pas besoin de savoir COMMENT la
// periode est choisie, seulement de reagir quand elle change.
interface AttendanceChartProps {
  period: AnalyticsPeriod;
}

export default function AttendanceChart({ period }: AttendanceChartProps) {
  // Le 2e argument `[period]` est la liste de dependances transmise a
  // `useAnalyticsData` : des que `period` change (l'utilisateur clique sur
  // un autre bouton du filtre), le hook relance automatiquement l'appel
  // API avec la nouvelle valeur — sans ca, changer le filtre ne
  // rafraichirait jamais les donnees affichees.
  const { data, isLoading, error } = useAnalyticsData(
    () => fetchAttendanceStats(period),
    [period]
  );

  // `useMemo` : on ne recalcule les statistiques que quand `data` change
  // reellement (nouvelle reponse API), pas a chaque rendu du composant
  // (ex: quand l'utilisateur redimensionne la fenetre). Pour 7 valeurs le
  // gain de performance est negligeable, mais c'est le bon reflexe a
  // prendre des qu'on derive des valeurs a partir de props/etat.
  const stats = useMemo(() => {
    if (!data || data.length === 0) return null;

    const total = data.reduce((sum, day) => sum + day.guests, 0);
    const average = total / data.length;

    // `reduce` pour trouver le jour avec le plus de convives, sans avoir a
    // trier tout le tableau (on ne veut que le maximum, pas l'ordre complet).
    const best = data.reduce(
      (max, day) => (day.guests > max.guests ? day : max),
      data[0]
    );

    return { total, average, best };
  }, [data]);

  return (
    <ChartCard
      title={`Frequentation (${PERIOD_LABELS[period]})`}
      isLoading={isLoading}
      error={error}
      isEmpty={!data || data.length === 0}
      // Badges de synthese affiches a cote du titre : donnent une lecture
      // immediate sans avoir a interpreter le graphique.
      headerExtra={
        stats && (
          <div className="flex gap-3 text-xs text-gray-500">
            <span>
              <strong className="text-primary">{stats.total}</strong> convives au total
            </span>
            <span>
              <strong className="text-primary">{stats.average.toFixed(1)}</strong> / jour en moyenne
            </span>
          </div>
        )
      }
    >
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data ?? []}>
          {/* `vertical={false}` : on ne trace que les lignes horizontales de
              la grille, plus lisible pour un graphique en barres (les
              lignes verticales n'apportent rien ici puisque chaque barre
              occupe deja sa propre colonne). */}
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="day" tick={{ fontSize: 12 }} />
          {/* `allowDecimals={false}` : un nombre de convives est toujours un
              entier, ca evite a Recharts de generer des graduations comme
              "2.5" sur l'axe vertical. */}
          <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
          <Tooltip
            formatter={(value: number) => [`${value} convives`, "Frequentation"]}
            labelFormatter={(label) => `Jour : ${label}`}
          />
          {/* ReferenceLine : trait horizontal pointille qui materialise la
              MOYENNE calculee plus haut. C'est ce qui transforme un simple
              histogramme en visualisation "statistiquement parlante" : en
              un coup d'oeil, le restaurateur voit quels jours sont
              au-dessus ou en-dessous de la normale, sans avoir a comparer
              les barres entre elles mentalement. */}
          {stats && (
            <ReferenceLine y={stats.average} stroke="#F59E0B" strokeDasharray="4 4">
              <Label value="Moyenne" position="insideTopRight" fill="#F59E0B" fontSize={11} />
            </ReferenceLine>
          )}
          <Bar dataKey="guests" fill="#3B82F6" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>

      {/* Phrase de synthese sous le graphique : met en mots ce que la
          ligne de reference montre visuellement, utile pour les
          utilisateurs qui survolent rapidement le dashboard sans analyser
          le graphique en detail. */}
      {stats && (
        <p className="text-xs text-gray-400 mt-2">
          Meilleur jour : <strong className="text-gray-600">{stats.best.day}</strong> avec{" "}
          {stats.best.guests} convives.
        </p>
      )}
    </ChartCard>
  );
}

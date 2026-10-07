// src/hooks/useAnalyticsData.ts (nouveau fichier)
"use client";

import { useEffect, useState } from "react";

// ============================================================================
// useAnalyticsData : hook generique pour charger UNE statistique analytics.
// ============================================================================
// Pourquoi un hook dedie plutot que de repeter `useState` + `useEffect`
// dans chaque graphique (AttendanceChart, PopularDishesChart,
// RevenueForecastChart) ? Parce que les 3 graphiques ont EXACTEMENT le
// meme besoin : appeler une fonction qui renvoie une Promise, savoir si on
// est en train de charger, savoir si ca a echoue (et pourquoi), et
// recuperer le resultat une fois pret. Centraliser cette logique ici evite
// de dupliquer 3 fois le meme code (principe DRY - "Don't Repeat
// Yourself"), et si on doit un jour ajouter un comportement commun (ex:
// reessayer automatiquement en cas d'echec reseau), on ne le fait qu'a un
// seul endroit.

interface UseAnalyticsDataResult<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
}

/**
 * Charge une statistique analytics via la fonction `fetchFn` fournie et
 * expose son etat de chargement (data / isLoading / error).
 *
 * Exemple d'utilisation dans un composant :
 *   const { data, isLoading, error } = useAnalyticsData(fetchAttendanceStats);
 */
export function useAnalyticsData<T>(
  fetchFn: () => Promise<T>,
  deps: unknown[] = []
): UseAnalyticsDataResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    setIsLoading(true);
    setError(null);

    fetchFn()
      .then((result) => {
        if (isMounted) {
          setData(result);
        }
      })
      .catch((err) => {
        console.error("[useAnalyticsData] Echec du chargement :", err);
        if (isMounted) {
          setError(
            "Impossible de charger les statistiques pour le moment. Verifiez votre connexion et reessayez."
          );
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, deps);

  return { data, isLoading, error };
}
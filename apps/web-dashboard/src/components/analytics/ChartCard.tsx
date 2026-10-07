// src/components/analytics/ChartCard.tsx (nouveau fichier)
"use client";

import type { ReactNode } from "react";
import Card from "@/components/ui/Card";
import Loader from "@/components/ui/Loader";

// ============================================================================
// ChartCard : coquille commune a tous les graphiques Analytics.
// ============================================================================
interface ChartCardProps {
  title: string;
  isLoading: boolean;
  error: string | null;
  isEmpty: boolean;
  children: ReactNode;
  headerExtra?: ReactNode;
}

export default function ChartCard({
  title,
  isLoading,
  error,
  isEmpty,
  children,
  headerExtra,
}: ChartCardProps) {
  return (
    <Card>
      <div className="flex items-center justify-between gap-2 flex-wrap mb-3">
        <h2 className="font-semibold">{title}</h2>
        {!isLoading && !error && headerExtra}
      </div>

      {isLoading ? (
        <Loader />
      ) : error ? (
        <p className="text-sm text-danger text-center py-10" role="alert">
          {error}
        </p>
      ) : isEmpty ? (
        <p className="text-sm text-gray-400 text-center py-10">
          Aucune donnee disponible pour le moment.
        </p>
      ) : (
        children
      )}
    </Card>
  );
}
// Petites fonctions utilitaires partagees

export function formatCurrency(amount: number, currency: "USD" | "CDF" = "USD") {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency,
  }).format(amount);
}

export function formatDate(dateStr: string) {
  return new Intl.DateTimeFormat("fr-FR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(dateStr));
}

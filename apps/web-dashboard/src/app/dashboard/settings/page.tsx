import SettingsPanel from "@/components/settings/SettingsPanel";

// La route reste un Server Component : seul le panneau interactif a besoin
// de "use client". Ce découpage garde la page lisible et ne modifie ni le
// layout partagé, ni les routes Salle, Réservations, Analytics ou le chat.
export default function SettingsPage() {
  return <SettingsPanel />;
}

"use client";
// "use client" obligatoire : ce composant est interactif (bouton Fermer,
// affichage conditionnel) donc il doit s'executer dans le navigateur.

import Modal from "@/components/ui/Modal";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import type { Reservation, RestaurantTable } from "@/lib/types";

// Meme principe que TableDetailsModal (src/components/dashboard/TableDetailsModal.tsx) :
// ce composant est purement "presentationnel", il affiche ce qu'on lui donne
// en props sans faire d'appel API lui-meme. C'est ReservationCalendar (le
// parent) qui va chercher les donnees et decider quelle reservation afficher.

// Traduit les statuts techniques (utilises cote API/base de donnees) en
// libelles lisibles pour le restaurateur.
const reservationStatusLabel: Record<Reservation["status"], string> = {
  PENDING_PAYMENT: "En attente de paiement",
  CONFIRMED: "Confirmee",
  CANCELLED: "Annulee",
  COMPLETED: "Terminee",
};

// Associe chaque statut de reservation a une couleur de Badge (voir Badge.tsx).
// Utile pour reperer visuellement en un coup d'oeil si une reservation est
// a risque (en attente de paiement, annulee) ou en ordre (confirmee).
const reservationStatusColor: Record<
  Reservation["status"],
  "success" | "accent" | "danger" | "primary"
> = {
  PENDING_PAYMENT: "accent",
  CONFIRMED: "success",
  CANCELLED: "danger",
  COMPLETED: "primary",
};

// ReservationDetailsModal = la fenetre modale qui s'ouvre quand on clique sur
// un evenement du calendrier des reservations (ReservationCalendar.tsx).
//
// props:
// - reservation : la reservation selectionnee, ou `null` si aucune modale ne
//                 doit s'afficher (meme logique que TableDetailsModal : c'est
//                 ce `null` qui pilote l'ouverture/fermeture de la modale)
// - table       : la table associee a cette reservation (via reservation.table_id),
//                 ou `null` si on ne l'a pas trouvee (table supprimee, pas encore
//                 assignee...). On l'affiche juste a titre informatif.
// - onClose     : fonction appelee pour fermer la modale
export default function ReservationDetailsModal({
  reservation,
  table,
  onClose,
}: {
  reservation: Reservation | null;
  table: RestaurantTable | null;
  onClose: () => void;
}) {
  return (
    // Meme pattern que pour les tables : la modale generique (Modal.tsx) gere
    // l'affichage/masquage, le fond sombre et le clic en dehors pour fermer.
    <Modal open={reservation !== null} onClose={onClose}>
      {/*
        Garde de securite : on ne rend le contenu detaille que si `reservation`
        n'est pas null, sinon TypeScript refuserait d'ecrire
        `reservation.customer_name` plus bas (le type autorise `null`).
      */}
      {reservation && (
        <div>
          {/* En-tete : nom du client + badge de statut de la reservation */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">
              {reservation.customer_name}
            </h2>
            <Badge color={reservationStatusColor[reservation.status]}>
              {reservationStatusLabel[reservation.status]}
            </Badge>
          </div>

          <dl className="text-sm space-y-1">
            <div className="flex justify-between">
              <dt className="text-gray-500">Telephone</dt>
              <dd className="font-medium">{reservation.customer_phone}</dd>
            </div>

            <div className="flex justify-between">
              <dt className="text-gray-500">Date / heure</dt>
              <dd className="font-medium">
                {new Date(reservation.reservation_date).toLocaleString("fr-FR", {
                  dateStyle: "full",
                  timeStyle: "short",
                })}
              </dd>
            </div>

            <div className="flex justify-between">
              <dt className="text-gray-500">Convives</dt>
              <dd className="font-medium">{reservation.guests_count}</dd>
            </div>

            <div className="flex justify-between">
              <dt className="text-gray-500">Table</dt>
              <dd className="font-medium">
                {table ? `${table.number_label} (${table.zone})` : "Non assignee"}
              </dd>
            </div>

            <div className="flex justify-between">
              <dt className="text-gray-500">Acompte verse</dt>
              <dd className="font-medium">{reservation.deposit_amount} $</dd>
            </div>

            <div className="flex justify-between">
              <dt className="text-gray-500">Code QR</dt>
              <dd className="font-medium font-mono text-xs">
                {reservation.qr_code_token}
              </dd>
            </div>
          </dl>

          <div className="mt-6 flex justify-end">
            <Button variant="secondary" onClick={onClose}>
              Fermer
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
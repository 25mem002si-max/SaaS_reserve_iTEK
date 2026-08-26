"use client";
// "use client" est obligatoire ici car ce composant utilise de l'interactivite
// (gestion de clic, affichage conditionnel base sur un state) : dans Next.js
// App Router, un composant est "Server Component" par defaut (rendu sur le
// serveur, pas de JS envoye au navigateur) sauf s'il declare explicitement
// qu'il doit tourner cote client.

import Modal from "@/components/ui/Modal";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import type { Reservation, RestaurantTable } from "@/lib/types";

// Ce composant ne fait AUCUN appel API lui-meme : il recoit tout en props
// (table, reservation) depuis FloorPlan, qui a deja fait le travail de
// recuperation des donnees. C'est une bonne pratique : on separe "aller
// chercher les donnees" (FloorPlan) de "les afficher" (TableDetailsModal).

// Associe chaque statut de TABLE a une couleur de badge (voir Badge.tsx).
// TypeScript nous oblige ici a couvrir TOUS les statuts possibles de
// RestaurantTable["status"] grace au typage Record<RestaurantTable["status"], ...>
// -> si un jour on ajoute un nouveau statut dans types.ts et qu'on oublie de
// l'ajouter ici, TypeScript nous previendra avec une erreur de compilation.
const statusBadgeColor: Record<
  RestaurantTable["status"],
  "success" | "accent" | "danger" | "primary"
> = {
  FREE: "success",
  RESERVED: "accent",
  OCCUPIED: "danger",
  LOCKED: "primary",
};

// Traduit les statuts techniques de RESERVATION (utilises en base de
// donnees / API, en anglais/majuscules) vers un libelle lisible en francais
// pour l'utilisateur final (le restaurateur).
const reservationStatusLabel: Record<Reservation["status"], string> = {
  PENDING_PAYMENT: "En attente de paiement",
  CONFIRMED: "Confirmee",
  CANCELLED: "Annulee",
  COMPLETED: "Terminee",
};

// TableDetailsModal = la fenetre modale (popup) qui s'ouvre quand on clique
// sur une table dans le plan de salle (FloorPlan -> TableCard -> ici).
//
// props:
// - table       : la table selectionnee, ou `null` si aucune modale ne doit
//                 s'afficher (c'est ce `null` qui pilote l'ouverture/fermeture,
//                 voir le composant Modal qui fait `if (!open) return null`)
// - reservation : la reservation associee a cette table si elle existe,
//                 sinon `null` (table libre, aucune reservation en cours)
// - onClose     : fonction appelee pour fermer la modale (remet `table` a null
//                 cote parent)
export default function TableDetailsModal({
  table,
  reservation,
  onClose,
}: {
  table: RestaurantTable | null;
  reservation: Reservation | null;
  onClose: () => void;
}) {
  return (
    // `open={table !== null}` : la modale ne s'affiche que si une table a ete
    // selectionnee. C'est le composant Modal (src/components/ui/Modal.tsx)
    // qui gere le fond noir semi-transparent, le clic en dehors pour fermer,
    // etc. On ne reinvente pas cette logique ici, on la reutilise.
    <Modal open={table !== null} onClose={onClose}>
      {/*
        On ne rend le contenu que si `table` existe (n'est pas null).
        Sans cette verification, TypeScript nous empecherait d'ecrire
        `table.number_label` plus bas car `table` pourrait techniquement
        etre `null` d'apres son type.
      */}
      {table && (
        <div>
          {/* En-tete : numero de la table + badge de statut colore */}
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">
              Table {table.number_label}
            </h2>
            <Badge color={statusBadgeColor[table.status]}>{table.status}</Badge>
          </div>

          {/*
            <dl>/<dt>/<dd> = "description list", la balise HTML semantique
            correcte pour afficher des paires cle/valeur (ici: "Zone" -> "VIP",
            "Capacite" -> "6 places", etc.) plutot que d'utiliser des <div>
            generiques sans signification.
          */}
          <dl className="text-sm space-y-1 mb-4">
            <div className="flex justify-between">
              <dt className="text-gray-500">Zone</dt>
              <dd className="font-medium">{table.zone}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Capacite</dt>
              <dd className="font-medium">{table.capacity} places</dd>
            </div>
          </dl>

          <hr className="my-4" />

          {/*
            Coeur de la logique : si une reservation existe pour cette table
            (reservation !== null), on affiche tous ses details. Sinon on
            affiche un simple message "table libre". C'est un rendu
            conditionnel classique en React avec l'operateur ternaire
            (condition ? siVrai : siFaux).
          */}
          {reservation ? (
            <div>
              <h3 className="text-sm font-semibold mb-2">Reservation en cours</h3>
              <dl className="text-sm space-y-1">
                <div className="flex justify-between">
                  <dt className="text-gray-500">Client</dt>
                  <dd className="font-medium">{reservation.customer_name}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Telephone</dt>
                  <dd className="font-medium">{reservation.customer_phone}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Date / heure</dt>
                  <dd className="font-medium">
                    {/*
                      reservation_date arrive du serveur comme une chaine de
                      caracteres ISO (ex: "2026-08-26T14:00:00.000Z").
                      new Date(...) la transforme en objet Date JavaScript,
                      puis .toLocaleString("fr-FR", {...}) l'affiche dans un
                      format lisible pour un utilisateur francophone
                      (ex: "26/08/2026 14:00") au lieu du format ISO brut.
                    */}
                    {new Date(reservation.reservation_date).toLocaleString("fr-FR", {
                      dateStyle: "short",
                      timeStyle: "short",
                    })}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Convives</dt>
                  <dd className="font-medium">{reservation.guests_count}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Acompte</dt>
                  <dd className="font-medium">{reservation.deposit_amount} $</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-500">Statut</dt>
                  <dd className="font-medium">
                    {/* On traduit le statut technique via le dictionnaire defini plus haut */}
                    {reservationStatusLabel[reservation.status]}
                  </dd>
                </div>
              </dl>
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              Aucune reservation associee - cette table est libre.
            </p>
          )}

          {/* Bouton de fermeture explicite, en plus du clic en dehors de la modale (gere par Modal.tsx) */}
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
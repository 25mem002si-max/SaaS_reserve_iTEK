"use client";
// "use client" obligatoire : ce composant utilise useState/useEffect
// (hooks React) et le WebSocket cote navigateur, ce qui n'est possible
// que dans un Client Component.

import { useEffect, useState } from "react";
import { getSocket } from "@/lib/websocket";
import { fetchTables, fetchReservations } from "@/lib/api";
import TableCard from "./TableCard";
import TableDetailsModal from "./TableDetailsModal";
import type { Reservation, RestaurantTable } from "@/lib/types";

// FloorPlan = le composant "chef d'orchestre" de la vue synoptique de la
// salle. C'est LUI qui :
//  1. va chercher les donnees (tables + reservations) au backend
//  2. ecoute les mises a jour temps reel via WebSocket
//  3. garde en memoire quelle table est actuellement selectionnee
//  4. delegue l'affichage a des composants "enfants" plus simples
//     (TableCard pour chaque carte, TableDetailsModal pour la popup de detail)
//
// C'est un pattern courant en React : le parent gere l'ETAT et la LOGIQUE,
// les enfants ne font qu'afficher ce qu'on leur donne (on dit qu'ils sont
// "presentationnels" ou "dumb components").
export default function FloorPlan() {
  // --- Les 3 "etats" (state) que ce composant doit retenir entre les rendus ---

  // Liste des tables du restaurant (recuperee via GET /tables)
  const [tables, setTables] = useState<RestaurantTable[]>([]);

  // Liste des reservations en cours (recuperee via GET /reservations)
  const [reservations, setReservations] = useState<Reservation[]>([]);

  // La table actuellement selectionnee par un clic utilisateur.
  // `null` = aucune table selectionnee = modale fermee.
  // C'est cette valeur qui pilote directement l'ouverture de TableDetailsModal.
  const [selectedTable, setSelectedTable] = useState<RestaurantTable | null>(null);

  // useEffect(..., []) = code execute UNE SEULE FOIS, juste apres le premier
  // affichage du composant (le tableau [] vide en 2eme argument = "pas de
  // dependances, ne relance jamais ce code automatiquement").
  // C'est l'endroit ideal pour : appels API initiaux + ouverture du WebSocket.
  useEffect(() => {
    // Appels REST classiques : on demande les donnees, et quand la reponse
    // arrive (.then), on met a jour le state avec setTables/setReservations,
    // ce qui declenche un nouveau rendu du composant avec les vraies donnees.
    // .catch(console.error) : si l'appel echoue (mock-server.js pas lance,
    // mauvaise URL...), on affiche juste l'erreur dans la console au lieu
    // de faire planter toute la page.
    fetchTables().then(setTables).catch(console.error);
    fetchReservations().then(setReservations).catch(console.error);

    // Connexion (ou reutilisation) du socket WebSocket partage, defini dans
    // src/lib/websocket.ts. C'est le meme socket que celui utilise par le
    // ChatWidget, socket.io gere une seule connexion sous le capot.
    const socket = getSocket();

    // On ecoute l'evenement "table_status_update" que le mock-server.js (ou
    // plus tard le vrai backend de Dev 2) emet quand le statut d'une table
    // change (nouvelle reservation, verrou Redis pose/libere, etc.)
    socket.on("table_status_update", (updated: RestaurantTable) => {
      // On met a jour UNIQUEMENT la table concernee dans la liste, en
      // remplacant l'ancienne version par la nouvelle (`updated`) grace a
      // .map() qui compare les id. Les autres tables restent inchangees.
      setTables((prev) =>
        prev.map((t) => (t.id === updated.id ? updated : t))
      );

      // Si la table qui vient d'etre mise a jour est justement celle
      // affichee dans la modale ouverte, on la met a jour aussi la-bas.
      // Sans cette ligne, la modale afficherait un statut "perime" (par
      // exemple encore "RESERVED" alors qu'elle vient de passer "OCCUPIED")
      // jusqu'a ce que l'utilisateur la ferme et la rouvre.
      setSelectedTable((prev) => (prev && prev.id === updated.id ? updated : prev));
    });

    // Fonction de "nettoyage" : React l'appelle automatiquement quand le
    // composant est retire de l'ecran (demontage), pour eviter les fuites
    // memoire (continuer a ecouter un evenement sur un composant qui n'existe
    // plus).
    return () => {
      socket.off("table_status_update");
    };
  }, []);

  // Calcul derive (pas un state a part) : on cherche dans le tableau des
  // reservations celle dont table_id correspond a la table selectionnee.
  // `selectedTable?.id` : optional chaining, evite un crash si selectedTable
  // est null (dans ce cas ?.id vaut undefined, et .find() ne trouvera rien
  // -> reservationForSelectedTable sera null grace au `?? null` final).
  const reservationForSelectedTable =
    reservations.find((r) => r.table_id === selectedTable?.id) ?? null;

  return (
    // Le fragment <>...</> permet de retourner deux elements freres (la grille
    // de tables + la modale) sans avoir a les envelopper dans une <div>
    // supplementaire inutile dans le DOM.
    <>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {/*
          .map() genere une TableCard par table du tableau `tables`.
          `key={table.id}` est obligatoire en React quand on affiche une
          liste : ca l'aide a savoir quel element a change/ete ajoute/retire
          sans tout redessiner a chaque mise a jour.
          `onClick={setSelectedTable}` : on passe directement la fonction
          setSelectedTable comme callback. Quand TableCard fera
          `onClick?.(table)`, ca appellera en realite setSelectedTable(table),
          ce qui declenchera l'ouverture de la modale pour cette table.
        */}
        {tables.map((table) => (
          <TableCard key={table.id} table={table} onClick={setSelectedTable} />
        ))}

        {/* Message affiche uniquement si l'appel API n'a encore rien retourne (chargement) ou si le restaurant n'a aucune table configuree */}
        {tables.length === 0 && (
          <p className="text-gray-500 text-sm col-span-full">
            Aucune table configuree pour le moment.
          </p>
        )}
      </div>

      {/*
        La modale est toujours "montee" dans le DOM, mais elle ne s'affiche
        visuellement que si `table` (premiere prop) n'est pas null - c'est
        TableDetailsModal + Modal qui gerent cette logique d'affichage.
        `onClose` remet selectedTable a null, ce qui referme la modale.
      */}
      <TableDetailsModal
        table={selectedTable}
        reservation={reservationForSelectedTable}
        onClose={() => setSelectedTable(null)}
      />
    </>
  );
}
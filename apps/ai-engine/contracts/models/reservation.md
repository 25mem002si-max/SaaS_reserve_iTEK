 # Contrat réservation

Une réservation contient au minimum une date/heure future, `guests_count` entre 1 et 50, un client identifié et une table verrouillée.

Statuts : `PENDING_PAYMENT`, `CONFIRMED`, `CANCELLED`, `COMPLETED`, `NO_SHOW`, `WAITING_LIST`.

Règle de cohérence : si la création backend échoue après verrouillage, le verrou doit être libéré. Une réservation avec acompte reste `PENDING_PAYMENT` jusqu’au paiement `SUCCESS`.

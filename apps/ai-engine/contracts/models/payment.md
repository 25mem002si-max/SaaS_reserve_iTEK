 # Contrat paiement

Fournisseurs autorisés : `m_pesa`, `orange_money`, `airtel_money`. Devises : `USD`, `CDF`.

## Cycle

1. L’AI Engine crée une demande avec `POST /api/payments`.
2. Le backend retourne `payment_id` et `PENDING`.
3. Le fournisseur confirme via webhook backend.
4. L’AI Engine lit `GET /api/payments/{payment_id}`.
5. Seul `SUCCESS` autorise la confirmation finale de l’acompte.

Statuts : `PENDING`, `SUCCESS`, `FAILED`, `REFUNDED`, `CANCELLED`, `EXPIRED`.

Les tokens et références fournisseur ne doivent jamais apparaître dans les logs publics.

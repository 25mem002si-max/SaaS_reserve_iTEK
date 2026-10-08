 # Contrat API AI Engine / Backend

Le backend Dev2 est la source de vérité pour les tables, réservations et paiements. L’AI Engine ne confirme jamais une disponibilité ou un paiement à partir d’une simulation.

## Configuration

```env
BACKEND_ENABLED=true
BACKEND_API_URL=http://backend:8000
BACKEND_API_KEY=<secret>
BACKEND_TIMEOUT_SECONDS=30
BACKEND_RETRY_COUNT=3
```

## Routes attendues

| Méthode | Route | Retry | Usage |
|---|---|---:|---|
| `POST` | `/api/availability` | Oui | Chercher les tables disponibles |
| `POST` | `/api/restaurants/{restaurant_id}/tables/{table_id}/lock` | Non | Verrouiller une table temporairement |
| `DELETE` | `/api/restaurants/{restaurant_id}/tables/{table_id}/lock` | Non | Libérer le verrou |
| `POST` | `/api/reservations` | Non | Créer la réservation |
| `POST` | `/api/payments` | Non | Initier un paiement Mobile Money |
| `GET` | `/api/payments/{payment_id}` | Oui | Lire le statut d’un paiement |

Les mutations doivent être idempotentes via un identifiant de requête transmis par le backend. Les erreurs `4xx` ne sont pas retentées ; les erreurs réseau et `5xx` ne le sont que pour les lectures.

## Sécurité et supervision

- `Authorization: Bearer <BACKEND_API_KEY>` sur chaque requête.
- Ne jamais journaliser un numéro de téléphone, token de paiement ou clé API en clair.
- Chaque requête doit pouvoir être corrélée avec `conversation_id`, `restaurant_id` et `request_id`.
- Une réservation est confirmée uniquement après réponse backend valide.

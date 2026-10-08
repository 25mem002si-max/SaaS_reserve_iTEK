 # Endpoints de référence

## Disponibilité

`POST /api/availability`

```json
{"restaurant_id":"restaurant-1","date":"2026-09-04T20:00:00","guests_count":4,"preferred_zone":"Terrasse"}
```

Réponse : objet `AvailabilityResult` avec `available`, `tables`, `date` et `guests_count`.

## Réservation

`POST /api/reservations`

Le payload contient `restaurant_id`, `table_id`, `customer_name`, `customer_phone`, `reservation_date`, `guests_count`, `preferences`, `allergies`, `deposit_amount` et `notes`.

Réponse : objet `ReservationConfirmation`. Une réponse invalide doit être rejetée par l’AI Engine.

## Erreurs

Réponses d’erreur recommandées : `{ "code": "TABLE_UNAVAILABLE", "message": "...", "request_id": "..." }`.

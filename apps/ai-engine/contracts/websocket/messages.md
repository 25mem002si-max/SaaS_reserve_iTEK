 # Messages WebSocket

Chaque message contient `conversation_id`, `message_id`, `type`, `timestamp` et `payload`.

Types client : `user_message`, `payment_confirmation`, `cancel_request`.

Types serveur : `assistant_message`, `clarification_required`, `reservation_pending_payment`, `reservation_confirmed`, `payment_pending`, `human_handoff`, `error`.

Les erreurs exposent un message compréhensible et un `request_id`, jamais une stack trace, un token ou une donnée personnelle complète.

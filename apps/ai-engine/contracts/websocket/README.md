 # Contrat WebSocket

Le WebSocket transporte les messages de conversation en temps réel. Le serveur doit authentifier la connexion, limiter la taille des messages et renvoyer un accusé de réception ou une erreur non technique.

Format commun :

```json
{"message_id":"msg-1","conversation_id":"conv-1","type":"assistant_message","timestamp":"2026-09-03T12:00:00Z","payload":{"content":"Votre réservation est en attente de paiement."}}
```

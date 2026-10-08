 # Contrat notifications

Une notification contient un type (`confirmation`, `reminder_24h`, `reminder_2h`, `payment_received`, `reservation_cancelled`), un canal (`whatsapp`, `sms`, `email`, `chat`), un destinataire et un `reservation_id`.

Le backend retourne `notification_id`, `sent`, `sent_at` et, en cas d’échec, un code d’erreur exploitable. Les envois peuvent être rejoués uniquement avec une clé idempotente `reservation_id + type + channel`.

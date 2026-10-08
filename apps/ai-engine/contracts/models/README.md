 # Modèles partagés

Les modèles documentés ici correspondent aux schémas Pydantic de `app/schemas`. Toute réponse backend doit être validée avant d’être utilisée par un agent.

Les champs sensibles (`customer_phone`, tokens, références de paiement) sont masqués dans les logs et ne sont jamais envoyés au LLM sans nécessité métier.

 # Template de contrat API

## Endpoint

- Méthode et route : `METHOD /path`
- Authentification : Bearer token
- Idempotence : obligatoire pour les mutations
- Timeout client : 30 secondes

### Requête

```json
{}
```

### Réponse succès

```json
{}
```

### Erreur

```json
{"code":"ERROR_CODE","message":"Message utilisateur","request_id":"request-1"}
```

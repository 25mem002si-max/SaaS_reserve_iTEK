# web-dashboard (Developpeur 3 - Frontend & Client Experience)

Application Next.js 14 (App Router) + TypeScript + Tailwind CSS.

## Perimetre
- Widget de chat client (connecte au backend via WebSocket)
- Dashboard restaurateur (plan de salle temps reel, calendrier, toggle agent IA)
- Analytics (frequentation, plats populaires, previsions de CA)
- Design system mobile-first

## Demarrage

```bash
npm install
cp .env.example .env.local   # puis renseigner les URLs fournies par le Dev 2
npm run dev
```

## Structure

Voir `src/app`, `src/components`, `src/lib`, `src/hooks`.

## Ne jamais commiter
Le fichier `.env.local` (cle secretes) - seul `.env.example` doit etre versionne.

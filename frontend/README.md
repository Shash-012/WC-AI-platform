# World Cup 2026 — AI Platform (Frontend)

Vite + React 19 + TypeScript. Tailwind CSS v4, React Router v6, light/dark themed,
with a cinematic parallax hero and an AI Scout chat wired to the Flask backend.

## Run

```bash
npm install
npm run dev      # http://localhost:5173  (proxies /scout -> localhost:5000)
npm run build    # type-check + production build to dist/
npm run preview  # serve the production build
```

The Scout page calls `POST /scout/chat`. Start the backend at `localhost:5000`
first; if it's down, the chat shows a friendly connection message.

## Routes

| Route          | Page                                            |
|----------------|-------------------------------------------------|
| `/`            | Home — parallax hero, stats, section links      |
| `/scout`       | AI Scout chat (stateless, history per request)  |
| `/groups`      | Groups A–H                                       |
| `/fixtures`    | 15 opening fixtures, grouped by date            |
| `/teams`       | Searchable grid of all 48 teams                 |
| `/teams/:id`   | Team detail — formation, key players, fixture    |
| `/predictor`   | Coming soon                                     |
| `/sentiment`   | Coming soon                                     |

"Ask Scout about this" CTAs on Teams/Fixtures/Groups deep-link to
`/scout?q=…`, pre-filling the chat input.

## Data

All non-chat data is static, parsed from `backend/data/*.txt` into typed
constants under `src/data/` (auto-generated; `src/data/lookups.ts` holds the
hand-written helpers). Key players are cross-referenced to each team by country,
and injury statuses are surfaced in the UI.

## Design tokens

Deep-navy / volt palette with an AA-safe light mode. Theme variables live in
`src/index.css`; toggle state persists in `localStorage`. Volt is reserved for
CTAs, active nav, and highlights — never body text on light backgrounds (a
separate `--color-accent-text` token keeps accent-colored text legible).

## React Bits-style components

`src/components/reactbits/` — ShinyText, SplitText, GradientText, Aurora,
AnimatedList. Icons are a self-contained inline set in `src/components/icons.tsx`.

# ATCON Home — scroll story hero

Static site, no build step. Everything served lives in `public/`:

- `index.html` — the page
- `atcon-ds.css` — ATCON design-system styles
- `assets/` — videos, images and logo
- `support.js`, `vendor/` — the runtime that renders the page
- `_headers` — Cloudflare caching and security headers

## Run locally

```
python -m http.server 8765 --directory public
```

Then open http://localhost:8765.

## Deploy to Cloudflare

**Option A — connect GitHub (deploys on every push)**

1. Cloudflare dashboard → Workers & Pages → Create → Import a repository.
2. Pick `sanskaratcon/atcon-films`.
3. Leave the build command empty. Cloudflare reads `wrangler.jsonc` and serves `public/`.

If you create it as a **Pages** project instead, set the build command to
empty and the build output directory to `public`.

**Option B — deploy from your computer**

```
npx wrangler login
npx wrangler deploy
```

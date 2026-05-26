# Coohom Help Center (Mintlify)

Coohom product knowledge base built with [Mintlify](https://mintlify.com).

## Structure

- `docs.json` — site configuration and multilingual navigation
- `knowledge/en/` — English articles (MDX)
- `knowledge/zh/` — Chinese articles (MDX)
- `knowledge/ja/` — Japanese articles (MDX)
- `markdown/` — legacy Markdown source (ignored by Mintlify; kept for reference)

## Local preview

```bash
npm i -g mint
mint dev
```

Open [http://localhost:3000](http://localhost:3000).

## Validate

```bash
mint validate
mint broken-links
```

## Migrate from markdown/

After updating files under `markdown/`, re-run:

```bash
python3 scripts/migrate_to_mintlify.py
```

Then merge `scripts/navigation-languages.json` into `docs.json` (or re-run the docs.json generation step in the migration workflow).

## AI tools

```bash
npx skills add https://mintlify.com/docs
```

Connect your deployed docs MCP at `https://<your-docs-domain>/mcp` in Cursor for documentation search.

## Deploy

Connect this repository in the [Mintlify dashboard](https://dashboard.mintlify.com) and install the GitHub app. Pushes to the default branch deploy automatically.

# Coohom Help Center (Mintlify)

Coohom product knowledge base built with [Mintlify](https://mintlify.com).

## Structure

- `docs.json` — site configuration and multilingual navigation
- `knowledge/en/` — English articles (MDX)
- `knowledge/zh/` — Chinese articles (MDX)
- `knowledge/ja/` — Japanese articles (MDX)
- `main.py` — sync articles from Help Center API (main entry)
- `scripts/` — sync implementation modules

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

## Sync from Help Center API (recommended)

Pull articles from Kujiale Help Center and write directly to `knowledge/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --days 7
```

Options (same semantics as Java `syncToMarkdown`):

| Flag | Default | Description |
|------|---------|-------------|
| `--days N` | 1 | Sync articles updated in the last N days |
| `--start-time` / `--end-time` | — | Epoch milliseconds (overrides `--days`) |
| `--only-publish` / `--no-only-publish` | publish only | Filter `PUBLISH` status |
| `--no-update-nav` | — | Skip regenerating `docs.json` |
| `--json` | — | Print result JSON |

After syncing, articles include a hidden `Assistant step guide` block (for AI indexing) with step text and image URLs. To refresh it on existing files:

```bash
python scripts/enrich_agent_media.py
```

**Important:** After changing content or `.mintlify/Assistant.md`, push to Git and wait for Mintlify to redeploy so the AI assistant re-indexes.

## AI tools

```bash
npx skills add https://mintlify.com/docs
```

Connect your deployed docs MCP at `https://<your-docs-domain>/mcp` in Cursor for documentation search.

## Deploy

Connect this repository in the [Mintlify dashboard](https://dashboard.mintlify.com) and install the GitHub app. Pushes to the default branch deploy automatically.

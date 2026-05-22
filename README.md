# honest-reviews

LLM-powered product comparison engine. Compare 2–5 tools for a specific use case via chat. Claims are sourced, cited, and human-reviewed.

## How it works

1. **Data layer** — `products/*.yaml` holds structured feature claims per product. Each claim links to a source URL with a date. Human-reviewed before merge.
2. **Evidence layer** — raw scraped content (vendor docs, G2, changelogs, Reddit) embedded in ChromaDB for RAG citations.
3. **Chat** — FastAPI `/chat` endpoint. Two steps: use case → candidates → deep comparison.

## Quickstart

```bash
# Install
uv venv && uv pip install -e ".[dev]"
cp .env.example .env
```

Edit `.env` and pick a provider — three options, uncomment one:

| Provider | Cost | Privacy | Setup |
|----------|------|---------|-------|
| **Ollama** (recommended) | Free | Fully local — no data leaves your machine | `ollama pull llama3.2` |
| **Groq** | Free tier | Cloud | [console.groq.com](https://console.groq.com) → API Keys |
| **OpenAI** | Paid | Cloud | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |

```bash
# Run the API
uv run uvicorn chat.main:app --reload

# Open the UI
open ui/index.html
```

## CLI tools

```bash
# Scrape vendor docs for a product
uv run scrape --product warmly --source vendor

# Suggest job tags for untagged features
uv run tag --product warmly

# Check for stale claims (>90 days)
uv run check-stale
```

## Adding a new product

1. Create `products/<slug>.yaml` — follow the schema in an existing file
2. Run `uv run scrape --product <slug> --source vendor` to generate a draft
3. Review `products/<slug>.draft.yaml`, merge reviewed claims into `<slug>.yaml`
4. Run `uv run tag --product <slug>` to get job tag suggestions
5. Edit `jobs:` arrays in the YAML, commit

## Contributing

- Claims must have a source URL and date
- No auto-merge of scraper output — always human-reviewed
- Job taxonomy lives in `jobs/taxonomy.yaml` — propose new jobs via PR
- Evidence (ChromaDB) is not committed; regenerated locally with `scrape`

## Tests

```bash
uv run pytest tests/ -v
```

## License

MIT — see [LICENSE](LICENSE).

# multimodal-hackathon

A template project for building agents on the [DigitalOcean Gradient AI Platform](https://docs.digitalocean.com/products/gradient-ai-platform/) using the Agent Development Kit (ADK).

## Setup

```bash
# Install the Gradient CLI
uv tool install gradient-adk

# Install project dependencies
uv sync

# Copy and fill in credentials
cp .env.example .env
```

Edit `.env` with your:
- `GRADIENT_MODEL_ACCESS_KEY` — from the Gradient AI Platform → Serverless Inference tab
- `DIGITALOCEAN_API_TOKEN` — personal access token with `genai` (CRUD) + `project` (read) scopes

Then initialise the agent config (sets workspace/deployment name in `.gradient/agent.yml`):

```bash
gradient agent init
```

## Development

```bash
# Run locally at http://0.0.0.0:8080/run
gradient agent run

# Test with curl
curl -X POST http://localhost:8080/run \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What time is it?"}'
```

## Deploy

```bash
gradient agent deploy
```

Deployment takes 1–5 minutes and returns a live endpoint URL.

```bash
curl -X POST https://agents.do-ai.run/v1/<uuid>/<deployment>/run \
  -H "Authorization: Bearer $DIGITALOCEAN_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!"}'
```

## Project structure

```
├── main.py                   # @entrypoint — start here
├── agents/                   # Agent logic modules
├── tools/                    # Custom @tool functions
├── .gradient/
│   ├── agent.yml             # Gradient CLI config (auto-managed)
│   └── .gradientignore       # Controls what is excluded from deploys
├── .env.example              # Credential template
└── requirements.txt          # Dependencies (mirrors pyproject.toml)
```

## Useful commands

| Command | Description |
|---|---|
| `gradient agent run` | Run locally with hot-reload |
| `gradient agent deploy` | Deploy to DigitalOcean |
| `gradient agent logs` | View runtime logs |
| `gradient agent traces` | Open traces UI |
| `gradient agent evaluate` | Run evaluations |

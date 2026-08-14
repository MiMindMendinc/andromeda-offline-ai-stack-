# Andromeda Local Gateway (Phase 1)

FastAPI policy gateway that sits in front of a local Ollama instance. It enforces
strict configuration, prompt-size limits, an explicit model allowlist, bounded
local audit logging, and API-key authentication whenever a key is configured.

## Endpoints

- `GET /health` — gateway status and Ollama reachability (`503` when degraded)
- `POST /api/generate` — `{ "prompt": "...", "model": "optional" }`

## Run

```bash
cd gateway
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp config.example.yaml config.yaml
python -m andromeda_gateway --config config.yaml
```

The default configuration listens only on loopback and allows only the default
model. A non-loopback bind requires both `allow_non_loopback_bind: true` and a
24+ character API key. Prefer supplying the key without writing it to disk:

```bash
export ANDROMEDA_API_KEY='replace-with-a-long-random-local-key'
```

Then:

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
curl -s http://127.0.0.1:8000/api/generate \
  -H 'content-type: application/json' \
  -d '{"prompt":"Say hello from Andromeda"}' | python3 -m json.tool
```

When a key is configured, add `-H "X-Andromeda-Key: $ANDROMEDA_API_KEY"` to
both requests.

## Tests

```bash
cd gateway
PYTHONPATH=. pytest -q
```

## Security

Binds to `127.0.0.1` by default. Non-loopback binds require an explicit opt-in
and API key. Keep this behind LAN firewall rules or WireGuard; do not expose it
publicly. The event log records metadata and bounded error details, never prompt
or response bodies, and retains at most `event_log_max_rows` records.

# Andromeda Local Gateway (Phase 1)

FastAPI policy gateway that sits in front of a local Ollama instance.

## Endpoints

- `GET /health` — gateway status and Ollama reachability
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

Then:

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
curl -s http://127.0.0.1:8000/api/generate \
  -H 'content-type: application/json' \
  -d '{"prompt":"Say hello from Andromeda"}' | python3 -m json.tool
```

## Tests

```bash
cd gateway
PYTHONPATH=. pytest -q
```

## Security

Binds to `127.0.0.1` by default. Non-loopback binds require `allow_non_loopback_bind: true`. Keep this behind LAN firewall rules or WireGuard; do not expose it publicly.

# Guardian Stack example

Minimal offline-first compose stack for local chat with pinned Ollama, Open WebUI,
Qdrant, and Caddy images. Every published port is host-only by default.

## Start

```bash
cd examples/guardian_stack
docker compose up -d
docker exec -it andromeda-ollama ollama pull llama3.2:3b
```

Open the dashboard at `http://localhost:3000` (or `http://localhost:8080` via Caddy).

## Security

- Ports bind to `127.0.0.1` only; other LAN hosts cannot connect by default.
- Open WebUI authentication is enabled; the first account created becomes admin.
- Do not publish Open WebUI or Ollama to the public internet.
- Use WireGuard (or similar) for remote admin access.
- Change defaults and enable auth before any shared or multi-user use.

## Offline use

Pull images and models while online, then disconnect. Core chat stays local after that first download.

## Next steps

See `docs/PI_DEPLOYMENT_GUIDE.md`, `docs/OFFLINE_FIRST_POLICY.md`, and `docs/SECURITY_CHECKLIST.md`.

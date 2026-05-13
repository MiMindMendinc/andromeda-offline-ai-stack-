# Andromeda Offline AI Stack

Privacy-first AI tools, local infrastructure, and deployment notes for family, farm, and edge devices.

Andromeda is an offline-first AI toolkit designed to bring local language models, speech processing, private document search, and automation to resource-constrained environments. The goal is simple: useful AI that can keep working when the internet is down and that keeps private data on the machine by default.

## Key features

- Private by default: core processing is local.
- Offline-first: works after models, packages, and containers are downloaded.
- Lightweight targets: Raspberry Pi, Jetson, mini PCs, old laptops, and local home servers.
- Modular: use only the pieces you need.
- Practical: focused on real deployment notes, not hype.

## Recommended first stack

```text
Ollama or llama.cpp
Open WebUI
FastAPI local gateway
SQLite
Qdrant or Chroma
whisper.cpp or Vosk
Piper
Caddy
WireGuard
Gitleaks, Syft, and Trivy for release checks
```

## Quick start

```bash
git clone https://github.com/MiMindMendinc/andromeda-offline-ai-stack-.git
cd andromeda-offline-ai-stack-
cd examples/guardian_stack
docker compose up -d
```

Open the local dashboard:

```text
http://localhost:3000
```

Before using the stack offline, pull a small local model:

```bash
docker exec -it andromeda-ollama ollama pull llama3.2:3b
```

## What this repo includes

```text
data/tools.json
docs/TOOL_CATALOG.md
docs/MINDMEND_STACK_RECOMMENDATION.md
docs/OFFLINE_FIRST_POLICY.md
docs/PI_DEPLOYMENT_GUIDE.md
docs/LORA_MESH_REALITY_CHECK.md
docs/SECURITY_CHECKLIST.md
docs/ROADMAP.md
scripts/tool_search.py
scripts/check_catalog.py
scripts/build_offline_bundle.sh
examples/guardian_stack/docker-compose.yml
```

## Use cases

### Private home assistant

A local voice or chat assistant that can answer questions, search local documents, and control local automations without requiring a cloud API by default.

### Farm and field monitoring

Sensors, cameras, or small field nodes send local status events into a home server. Heavy AI runs on the home server; small nodes handle short messages and alerts.

### Offline family knowledge base

Local documents, notes, manuals, and journals can be indexed into a private search system. Sensitive data should stay local and encrypted where appropriate.

## LoRa reality check

LoRa is useful for tiny status messages, sensor readings, and alerts. It is not a good transport for streaming voice, video, model files, or full AI chat sessions.

## Security rule

Do not expose local dashboards directly to the public internet. Use LAN-only access, firewall rules, or a private VPN such as WireGuard.

## License

MIT for this repository's original documentation and scripts. Upstream tools keep their own licenses and must be reviewed separately.

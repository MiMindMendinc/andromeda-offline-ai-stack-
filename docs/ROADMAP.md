# Roadmap

## Phase 0: Repo foundation

- README
- Tool catalog (`docs/TOOL_CATALOG.md` + `data/tools.json`)
- Offline-first policy
- Pi guide
- LoRa notes
- Security checklist
- Catalog scripts (`scripts/tool_search.py`, `scripts/check_catalog.py`, `scripts/build_offline_bundle.sh`)
- Docker example (`examples/guardian_stack`)

## Phase 1: Local gateway

- FastAPI gateway (`gateway/`)
- `/health` endpoint
- `/api/generate` endpoint
- Ollama adapter
- Local config file (`gateway/config.example.yaml`)
- SQLite event log
- Basic tests (`gateway/tests`)

## Phase 2: Voice loop

- Wake word
- Speech-to-text
- Local intent routing
- Text-to-speech
- Physical mute mode

## Phase 3: RAG memory

- Local document ingestion
- Embeddings
- Qdrant or Chroma storage
- Search endpoint
- Source-aware responses

## Phase 4: Home and farm automations

- MQTT bridge
- Home Assistant integration
- Node-RED examples
- Sensor event examples
- Human confirmation for risky actions

## Phase 5: Field-node network

- Meshtastic notes
- LoRa payload formats
- Node health dashboard
- Offline sync strategy
- Battery and solar field guide

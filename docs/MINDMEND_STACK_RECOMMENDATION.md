# MindMend Stack Recommendation

This is the practical build order for Andromeda.

## Tier 1: Guardian Pi prototype

Use this for a small offline voice assistant, safety demo, or family/farm command node.

```text
Raspberry Pi 5, 8GB
USB microphone or ReSpeaker-style mic
Small speaker
Physical mute switch
Ollama with small model, or remote LAN Ollama server
Vosk or whisper.cpp
Piper TTS
SQLite logs
FastAPI policy gateway
```

Best use: simple local Q&A, commands, reminders, local knowledge base, and home/farm automation.

## Tier 2: Home AI server

Use this as the heavy brain for the house/farm.

```text
Mini PC, old gaming PC, workstation, or Mac
Ollama / llama.cpp / LocalAI
Open WebUI
Qdrant or Chroma
Syncthing for controlled file sync
WireGuard for private remote admin
Caddy for local reverse proxy
```

Best use: bigger local models, RAG over documents, private chat UI, multiple local devices connecting over LAN.

## Tier 3: Field nodes

Use these for farms, sheds, barns, vehicles, greenhouses, and remote property edges.

```text
ESP32 / Raspberry Pi Zero / Meshtastic node
MQTT or LoRa messages
Battery/solar option
Sensor payloads only
Tiny commands, alerts, and status pings
```

Best use: event detection, status, emergency pings, and sensor readings. Do not try to stream voice, video, or full LLM chats over LoRa.

## Default recommendation

Start with a home AI server plus one Raspberry Pi voice node. Add field nodes only after the local assistant and dashboard are stable.

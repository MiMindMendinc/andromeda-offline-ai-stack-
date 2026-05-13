# Raspberry Pi Deployment Guide

## Recommended hardware

- Raspberry Pi 5, 8GB preferred
- Active cooling
- 64GB or larger storage
- USB microphone
- Small speaker
- Reliable power supply

## Good Pi roles

- Wake word listener
- Local command assistant
- Sensor hub
- Home Assistant node
- Piper text-to-speech output
- Vosk command recognition
- Small local RAG client

## Heavy workloads to avoid on Pi

- Large LLM inference
- Image generation
- Heavy video analysis
- Multiple users at once

## Suggested voice path

```text
openWakeWord
Vosk or whisper.cpp
FastAPI local gateway
Ollama on Pi for small models, or Ollama on LAN server
Piper TTS
```

## Setup pattern

1. Install Raspberry Pi OS Lite.
2. Update packages.
3. Install Docker.
4. Clone this repo.
5. Start only the services you need.
6. Pull small models first.
7. Test offline after the first successful model pull.

## Practical advice

Use the Pi for input, output, sensors, and local commands. Use a mini PC or home server for the heavier AI work when possible.

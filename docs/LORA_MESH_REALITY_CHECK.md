# LoRa Mesh Reality Check

LoRa is useful for tiny messages. It is not a replacement for broadband internet.

## Good LoRa jobs

- Sensor readings
- Device health pings
- Short commands
- Battery status
- Gate, barn, shed, and field alerts
- Location or status messages

## Poor LoRa jobs

- Streaming voice
- Streaming video
- Sending model files
- Full chatbot conversations
- Large document sync
- High-speed web browsing

## Best Andromeda pattern

```text
Remote node: sensor, button, display, short command
LoRa mesh: tiny message transport
Home server: AI reasoning and storage
LAN or scheduled sync: large files and updates
```

## Practical rule

Let LoRa move tiny facts. Let the home server do the thinking.

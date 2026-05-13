# Security Checklist

Use this before calling a release ready.

## Local network

- Keep dashboards LAN-only unless a private VPN is used.
- Do not publish Open WebUI, Ollama, Qdrant, or Home Assistant directly to the public internet.
- Use firewall rules on the host.
- Change default passwords.
- Keep SSH key-based and limited to trusted devices.

## Data

- Keep private documents local.
- Encrypt backups.
- Keep logs minimal.
- Do not store raw voice recordings unless the user clearly enables it.
- Separate demo data from real family or client data.

## Repo hygiene

- Run secret scanning before release.
- Do not commit `.env` files.
- Document every upstream tool license.
- Pin important dependency versions.
- Keep a bill of materials for production deployments.

## AI safety

- Add a local policy gateway before tool calls.
- Do not let models directly control devices without validation.
- Add human confirmation for risky automation.
- Mental-health-adjacent flows must route crisis language to human support and emergency resources.

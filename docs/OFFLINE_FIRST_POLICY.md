# Offline-First Policy

Andromeda systems must default to local execution and local storage.

## Hard rules

1. Private prompts, child/family conversations, journals, voice recordings, and local knowledge-base documents stay on the device by default.
2. Cloud providers are optional connectors, not default dependencies.
3. Every model, embedding tool, and vector store must document whether it can run offline.
4. Device logs must be local, minimal, and encrypted when sensitive.
5. Remote admin access must use private networking, strong keys, and least privilege.
6. Mental-health-adjacent flows must clearly state they are not therapy or emergency care and must route crisis language to human/emergency resources.

## Preferred path

```text
User
 -> Local UI or voice interface
 -> Local safety gate
 -> Local LLM / RAG
 -> Local response validator
 -> Local encrypted logs
```

## Cloud exception

A cloud connector is allowed only when:

- the user explicitly enables it,
- the UI clearly labels it,
- sensitive data is redacted or withheld when possible,
- the local fallback still works without internet.

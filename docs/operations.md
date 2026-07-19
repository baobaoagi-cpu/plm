# Operations

- Never commit `.env` or provider credentials.
- Use a secret manager in production.
- Use an isolated LiveKit project and secret prefix for each deployed persona/environment.
- Do not log API keys, access tokens, full Voice IDs, raw audio, or full prompts by default.
- Audio dumps are disabled by default and require an explicit retention and privacy policy.
- Initialize heavyweight models inside the runtime entrypoint or lazily, not at module import.


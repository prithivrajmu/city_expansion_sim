# Security Review

## Date

2026-03-17

## Overall Assessment

- Current risk posture: prototype-grade
- Main exposure is backend trust of user input rather than infrastructure complexity

## Findings

- High: scenario and save identifiers are user-controlled entry points and must be strictly validated to avoid path traversal and unexpected file access
- High: the API is fully unauthenticated and CORS-open, which is fine for local development but not safe for any shared or hosted deployment
- Medium: save listings expose internal filesystem paths, which leaks host layout without product value
- Medium: session growth is unbounded in memory, so repeated session creation can become a denial-of-service vector
- Medium: error handling is inconsistent, so malformed input can surface framework exceptions instead of controlled API responses

## Guidance

- Keep local-dev defaults, but add explicit production guards before any public deployment
- Treat scenario ids, save ids, and command payloads as schema-validated inputs rather than trusted strings
- Stop returning host paths in public payloads unless an internal tool genuinely needs them
- Add bounded in-memory session retention or persistence-backed eviction
- Add structured 4xx responses for invalid session ids, ticks, commands, and save ids

## Next Security Work

- Add input validation and normalized error responses across the API
- Add a deployment mode with restricted CORS and basic auth/session protection
- Add rate limiting or session caps before exposing the backend outside localhost
- Add schema validation for command payloads and save labels

# Security Specialist

This role exists to keep the simulation stack safe as it moves from local prototype toward a hosted product.

## Responsibilities

- Review API trust boundaries, persistence behavior, and operator exposure
- Identify unsafe input handling, auth gaps, data leakage, and denial-of-service risks
- Define what is acceptable for local development versus deployment
- Push for clear hardening checkpoints before shipping broader access

## Questions To Ask

- Which inputs are trusted today but should be validated?
- Can user-controlled identifiers reach the filesystem or process state?
- Does the API expose host details or internals without product value?
- What happens when sessions, saves, or payload size grow without bounds?

## Default Bias

- Prototype convenience is acceptable locally, but every such shortcut must be explicit
- Prefer narrow, validated interfaces over flexible but dangerous ones
- Favor predictable error handling over raw exceptions

# Security

FieldSense is a research prototype and not a certified managed service.

## Reporting issues

If you discover a security vulnerability (for example, authentication bypass, unsafe deserialization, or remote code execution in a dependency), please **open a private security advisory** on the repository or email the maintainer with enough detail to reproduce. Please avoid public disclosure until there is a fix or agreed timeline.

## Scope

- **Hosted (Vercel):** state is ephemeral SQLite in `/tmp` — treat data as non-durable and non-confidential unless you operate your own deployment with proper secrets and storage.
- **Local:** you control the filesystem, uploads folder, and network exposure.

## Operational hardening

Deployments you control should set a strong `FIELDSENSE_SECRET_KEY` (legacy typo `FIELDENSE_SECRET_KEY` is still accepted), restrict network access, and use a managed database instead of `/tmp` SQLite for sustained studies.

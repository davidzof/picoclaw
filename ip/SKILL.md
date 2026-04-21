---
name: ip
description: Get the current public IP address and rough geolocation.
homepage: https://ipapi.co/json/
metadata: {"nanobot":{"emoji":"🌍","requires":{"bins":["curl"]}}}
---

# Public IP

Use this skill to get the current public IP address and rough geolocation of the machine running PicoClaw.

## Rules

- Always use `curl` via `exec`.
- Always query the JSON endpoint below.
- Do not answer from memory.
- Do not use the `homepage` field as input data.
- Do not write to any file.
- Never modify this SKILL.md file.
- Return the answer directly in chat.
- If the request fails or returns empty output, say that the public IP could not be determined.

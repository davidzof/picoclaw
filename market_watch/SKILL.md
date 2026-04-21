---
name: market
description: get the current news about the market
metadata: {"nanobot":{"emoji":"🌍","requires":{"bins":["python3"]}}}
---

## Purpose

This skill identifies macroeconomic and geopolitical drivers behind recent market movements.

Use it to explain WHY stocks are moving.

---

## When to use

- When stocks show strong or unusual moves
- When multiple stocks move together
- When the user asks "why is the market moving?"

---

# Command:

## Command-line usage

Run in directory:

skills/market_watch

### Text output

```bash
python3 market_watch.py -t <TICKER1> <TICKER2> ... --json

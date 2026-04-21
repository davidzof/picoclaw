# Daily Stock Brief Skill

## Purpose

This skill generates a minimal daily stock analysis for one or more ticker symbols using Yahoo Finance data via `yahooquery`.

It is designed to be:
- simple
- deterministic
- easy to extend
- suitable for agent workflows

The skill does not provide financial advice. It only summarizes recent price and volume behavior.

---

## When to use this skill

Use this skill when the user asks to:
- analyze one or more stocks
- compare recent stock performance
- get a daily or short-term market brief
- evaluate momentum, trend, or volume behavior

Examples:
- "Analyze AAPL"
- "Compare AAPL MSFT NVDA"
- "Give me a daily brief for AI.PA MC.PA OR.PA"

---

## Inputs

The skill accepts:

- one ticker or multiple tickers
- optional history period
- optional data interval

### Example inputs

- `AAPL`
- `AAPL MSFT NVDA`
- `AI.PA MC.PA OR.PA`

Optional parameters:

- `period`: default `3mo`
- `interval`: default `1d`

---
## CRITICAL OUTPUT FORMAT RULES

When analyzing multiple tickers, you MUST follow this structure.

### REQUIRED STRUCTURE

Your response MUST:

1. Start with a short overall summary (1–2 sentences)
2. Identify the strongest and weakest stocks
3. Describe common trends across all tickers
4. Comment on volume behavior across the group
5. End with a short descriptive conclusion

---

### REQUIRED STYLE

- Write in paragraphs (NOT bullet lists per ticker)
- DO NOT repeat all metrics for each ticker
- DO NOT produce one paragraph per ticker
- DO NOT restate the table row-by-row

---

### REQUIRED COMPARISON

You MUST explicitly compare tickers:

- Identify the strongest 5-day performer
- Identify any outliers
- Group similar performers together

---

### REQUIRED PHRASING

Use phrasing like:

- "X is the strongest recent mover"
- "All names are trading above their 20-day moving average"
- "The group shows similar moderate strength"
- "Volume is consistently light across the group"

---

### FORBIDDEN PATTERN

DO NOT produce output like:

- "AAPL has X, MSFT has Y, NVDA has Z"
- one paragraph per ticker
- full repetition of all metrics

This is considered incorrect output.

---

### EXAMPLE OF GOOD OUTPUT

Example:

All four stocks are trading above their 20-day moving average, which is why they are all flagged as extended_up.

SOI.PA clearly stands out as the strongest recent mover, with a much larger 5-day gain than the rest of the group. The other three names — AKE.PA, SOLB.BR, and AI.PA — show similar but more moderate upward moves.

A common feature across all four stocks is that they are extended above their recent averages, indicating short-term strength.

However, volume is light across the group, suggesting that the move is not strongly supported by trading activity.

Overall, the group shows upward extension led by SOI.PA, with weaker confirmation from volume.

---

### INTERPRETATION RULES

- Be descriptive, not predictive
- Do NOT say a stock is "due for a correction"
- Do NOT give financial advice
- Signals are descriptive only, not forecasts
---
## Command-line usage

Run in directory:

skills/brief

Command:

### Text output

```bash
python3 brief.py -t <TICKER1> <TICKER2> ... --json

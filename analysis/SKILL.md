# Analysis Skill

## Purpose

Analyze one or more stocks and explain both:

- what the stocks did (price, trend, volume)
- why they are moving (macro / market context)

This skill combines:
- `brief.py` (stock analysis)
- `market_watch.py` (macro/news context)

---

## When to use

Use this skill when the user asks to:
- analyze stocks
- compare stocks
- explain why stocks are moving
- get a daily stock brief

Examples:
- "Analyze AAPL"
- "Compare AAPL MSFT NVDA"
- "Why are SOI.PA and AKE.PA moving?"
- "Give me a daily brief on these stocks"

---

## Inputs

- one or more ticker symbols

Example:
AAPL MSFT NVDA

---

## Execution steps (MANDATORY)

You MUST follow these steps exactly.

### Step 1 — Run stock analysis

python3 skills/brief/brief.py -t <TICKERS> --json

Store the JSON output as:
stock_data

---

### Step 2 — Run market context

python3 skills/market_watch/market_watch.py --json

Store the JSON output as:
market_data

---

## Final answer (CRITICAL)

You MUST combine stock_data and market_data into ONE integrated answer.

---

## REQUIRED STRUCTURE

Your answer MUST have exactly 3 paragraphs:

### Paragraph 1 — Stock behavior
- summarize the group
- identify the strongest stock
- identify any outlier
- mention common signal (e.g. all extended_up)
- mention volume pattern

### Paragraph 2 — Market context
- state the main macro driver
- mention key theme (oil, war, inflation, etc.)

### Paragraph 3 — Connection (MOST IMPORTANT)
- explain why the macro driver fits these stocks
- say if the move is macro-driven or stock-specific
- use the stock data as evidence

---

## REQUIRED STYLE

- Write in paragraphs (NOT bullet points)
- Compare stocks instead of listing them
- Focus on group behavior, not individual repetition

---

## DO NOT

- Do NOT repeat one paragraph per ticker
- Do NOT restate raw metrics line-by-line
- Do NOT summarize each script separately
- Do NOT give financial advice
- Do NOT predict future price direction

---

## REQUIRED LANGUAGE

Use phrasing like:
- "X is the strongest recent mover"
- "All names are trading above their 20-day moving average"
- "The group shows similar moderate strength"
- "Volume is light across the group"
- "This move appears to be macro-driven"
- "This fits the stock data because..."

---

## ERROR HANDLING

- If one script fails, still return the other result
- Clearly state if data is missing
- Do NOT invent data

---

## GOAL

The final answer should read like a short analyst note:
- clear
- structured
- explanatory
- not just descriptive

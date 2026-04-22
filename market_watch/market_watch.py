#!/usr/bin/env python3
import argparse
import json
import re
import sys
import urllib.parse
from collections import Counter
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any


import feedparser
from yahooquery import Ticker

GOOGLE_NEWS_BASE = (
    "https://news.google.com/rss/search?"
    "q={query}&hl=en-US&gl=US&ceid=US:en"
)

DEFAULT_MACRO_QUERY = "oil war ceasefire inflation rates energy site:reuters.com"

SOURCE_PRIORITY = {
    "reuters": 3,
    "yahoo_finance": 2,
    "other": 1,
}

QUERY_MAX_AGE_DAYS = {
    "company_reuters": 7,
    "company_context_reuters": 7,
    "industry_reuters": 7,
    "sector_reuters": 5,
    "group_sector_reuters": 5,
    "group_industry_reuters": 5,
    "ticker_yahoo": 7,
    "company_yahoo": 7,
    "macro_reuters": 3,
}

PER_TICKER_MAX_GROUPS = 3
GROUP_MAX_GROUPS = 6

SECTOR_HINTS = {
    "technology": ["semiconductor", "chip", "electronics"],
    "basic materials": ["chemicals", "materials", "industrial"],
    "industrials": ["industrial", "manufacturing", "energy costs"],
    "energy": ["oil", "gas", "refining"],
    "utilities": ["power", "gas", "electricity"],
    "consumer cyclical": ["consumer demand", "autos", "retail"],
    "consumer defensive": ["food", "pricing", "demand"],
    "healthcare": ["pharma", "biotech", "medical devices"],
    "financial services": ["rates", "credit", "banking"],
    "real estate": ["property", "rates", "construction"],
    "communication services": ["media", "telecom", "advertising"],
}


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    output = []
    for item in items:
        key = item.strip().lower()
        if key and key not in seen:
            output.append(item)
            seen.add(key)
    return output


def normalize_tickers(tickers: list[str]) -> list[str]:
    cleaned = [clean_text(t).upper() for t in tickers if clean_text(t)]
    return dedupe_preserve_order(cleaned)


def extract_company_name_from_summary(summary: str) -> str:
    if not summary:
        return ""
    first_sentence = summary.split(".")[0].strip()
    if len(first_sentence) > 120:
        return ""
    return first_sentence


def get_company_metadata(tickers: list[str]) -> dict[str, dict[str, str]]:
    tq = Ticker(tickers)
    asset_profiles = tq.asset_profile
    quote_types = tq.quote_type

    metadata: dict[str, dict[str, str]] = {}

    for symbol in tickers:
        ap = asset_profiles.get(symbol, {}) if isinstance(asset_profiles, dict) else {}
        qt = quote_types.get(symbol, {}) if isinstance(quote_types, dict) else {}

        long_name = clean_text(qt.get("longName"))
        short_name = clean_text(qt.get("shortName"))
        summary = clean_text(ap.get("longBusinessSummary"))
        inferred_name = extract_company_name_from_summary(summary)

        metadata[symbol] = {
            "symbol": symbol,
            "company_name": long_name or short_name or inferred_name or symbol,
            "sector": clean_text(ap.get("sector")),
            "industry": clean_text(ap.get("industry")),
            "quote_type": clean_text(qt.get("quoteType")),
        }

    return metadata


def make_google_news_url(query: str) -> str:
    return GOOGLE_NEWS_BASE.format(query=urllib.parse.quote_plus(query))


def sector_hint_terms(sector: str) -> list[str]:
    if not sector:
        return []
    return SECTOR_HINTS.get(sector.lower(), [])


def parse_entry_datetime(entry: Any) -> datetime | None:
    for attr in ("published", "updated"):
        value = getattr(entry, attr, None)
        if value:
            try:
                dt = parsedate_to_datetime(value)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except Exception:
                pass

    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime(*parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pass

    return None


def age_in_days(dt: datetime | None) -> float | None:
    if dt is None:
        return None
    return (datetime.now(timezone.utc) - dt).total_seconds() / 86400.0


def matches_company(title: str, company_name: str, symbol: str) -> bool:
    lower = title.lower()
    company_tokens = [t for t in re.split(r"[\s\-/&,().]+", company_name.lower()) if len(t) >= 4]
    if symbol and symbol.lower() in lower:
        return True
    return any(token in lower for token in company_tokens[:4])


def classify_driver_from_text(text: str) -> list[str]:
    lower = text.lower()
    drivers = []

    if any(word in lower for word in ["oil", "gas", "energy", "refining", "crude"]):
        drivers.append("Oil and energy market volatility")
    if any(word in lower for word in ["iran", "war", "ceasefire", "sanctions", "middle east", "hormuz"]):
        drivers.append("Geopolitical tensions and conflict-related de-escalation/escalation")
    if any(word in lower for word in ["inflation", "rates", "rate cut", "rate hike", "central bank", "fed", "ecb"]):
        drivers.append("Interest-rate and inflation expectations")
    if any(word in lower for word in ["supply", "supply chain", "exports", "blockade", "shipping"]):
        drivers.append("Supply disruption and trade-flow concerns")
    if any(word in lower for word in ["chip", "semiconductor"]):
        drivers.append("Semiconductor sector developments")
    if any(word in lower for word in ["chemical", "chemicals", "materials"]):
        drivers.append("Chemicals and materials sector developments")
    if any(word in lower for word in ["industrial", "manufacturing", "factory"]):
        drivers.append("Industrial sector repricing")

    return drivers


def relevance_score(
    title: str,
    source: str,
    symbol: str | None,
    company_name: str,
    sector: str,
    industry: str,
    age_days: float | None,
) -> float:
    score = 0.0
    lower = title.lower()

    score += SOURCE_PRIORITY.get(source, 1) * 10

    if symbol and symbol.lower() in lower:
        score += 18

    if company_name and matches_company(title, company_name, symbol or ""):
        score += 18

    if sector and sector.lower() in lower:
        score += 6

    if industry and industry.lower() in lower:
        score += 8

    for kw in ("oil", "energy", "war", "ceasefire", "inflation", "rates", "iran", "sanctions", "hormuz"):
        if kw in lower:
            score += 3

    if age_days is not None:
        if age_days <= 1:
            score += 8
        elif age_days <= 3:
            score += 5
        elif age_days <= 7:
            score += 2
        else:
            score -= 20

    return score


def build_queries(metadata: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    queries: list[dict[str, Any]] = []

    sectors = []
    industries = []

    for symbol, info in metadata.items():
        company = info["company_name"]
        sector = info["sector"]
        industry = info["industry"]

        if sector:
            sectors.append(sector.lower())
        if industry:
            industries.append(industry.lower())

        if company and company != symbol:
            queries.append({
                "type": "company_reuters",
                "source": "reuters",
                "symbol": symbol,
                "company_name": company,
                "query": f'"{company}" site:reuters.com',
            })

        if company and sector and industry:
            queries.append({
                "type": "company_context_reuters",
                "source": "reuters",
                "symbol": symbol,
                "company_name": company,
                "query": f'"{company}" {sector} {industry} site:reuters.com',
            })

        if industry:
            queries.append({
                "type": "industry_reuters",
                "source": "reuters",
                "symbol": symbol,
                "company_name": company,
                "query": f'{industry} site:reuters.com',
            })

        if sector:
            hints = " ".join(sector_hint_terms(sector)[:2])
            queries.append({
                "type": "sector_reuters",
                "source": "reuters",
                "symbol": symbol,
                "company_name": company,
                "query": f'{sector} {hints} site:reuters.com'.strip(),
            })

        queries.append({
            "type": "ticker_yahoo",
            "source": "yahoo_finance",
            "symbol": symbol,
            "company_name": company,
            "query": f'{symbol} site:finance.yahoo.com',
        })

        if company and company != symbol:
            queries.append({
                "type": "company_yahoo",
                "source": "yahoo_finance",
                "symbol": symbol,
                "company_name": company,
                "query": f'"{company}" site:finance.yahoo.com',
            })

    if sectors:
        common_sector = Counter(sectors).most_common(1)[0][0]
        hints = " ".join(SECTOR_HINTS.get(common_sector, [])[:2])
        queries.append({
            "type": "group_sector_reuters",
            "source": "reuters",
            "symbol": None,
            "company_name": "",
            "query": f'{common_sector} {hints} oil energy site:reuters.com'.strip(),
        })

    if industries:
        common_industry = Counter(industries).most_common(1)[0][0]
        queries.append({
            "type": "group_industry_reuters",
            "source": "reuters",
            "symbol": None,
            "company_name": "",
            "query": f'{common_industry} site:reuters.com',
        })

    queries.append({
        "type": "macro_reuters",
        "source": "reuters",
        "symbol": None,
        "company_name": "",
        "query": DEFAULT_MACRO_QUERY,
    })

    return queries


def fetch_feed_entries(
    query: str,
    source: str,
    symbol: str | None,
    company_name: str,
    sector: str,
    industry: str,
    max_age_days: int,
    keep_limit: int,
) -> tuple[list[dict[str, Any]], int]:
    url = make_google_news_url(query)
    feed = feedparser.parse(url)

    kept: list[dict[str, Any]] = []
    stale_removed = 0

    for entry in feed.entries:
        dt = parse_entry_datetime(entry)
        days_old = age_in_days(dt)

        if dt is None or (days_old is not None and days_old > max_age_days):
            stale_removed += 1
            continue

        title = clean_text(getattr(entry, "title", ""))
        link = clean_text(getattr(entry, "link", ""))
        if not title:
            continue

        score = relevance_score(
            title=title,
            source=source,
            symbol=symbol,
            company_name=company_name,
            sector=sector,
            industry=industry,
            age_days=days_old,
        )

        kept.append({
            "title": title,
            "link": link,
            "published": dt.isoformat() if dt else "",
            "age_days": round(days_old, 2) if days_old is not None else None,
            "score": round(score, 2),
            "drivers": classify_driver_from_text(title),
        })

    kept.sort(key=lambda x: (-x["score"], x["age_days"] if x["age_days"] is not None else 9999))
    return kept[:keep_limit], stale_removed


def build_news_results(
    queries: list[dict[str, Any]],
    metadata: dict[str, dict[str, str]],
    per_query_limit: int = 3,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    results: list[dict[str, Any]] = []
    stale_removed_total = 0

    for q in queries:
        symbol = q["symbol"]
        info = metadata.get(symbol, {}) if symbol else {}

        entries, stale_removed = fetch_feed_entries(
            query=q["query"],
            source=q["source"],
            symbol=symbol,
            company_name=q.get("company_name", info.get("company_name", "")),
            sector=info.get("sector", ""),
            industry=info.get("industry", ""),
            max_age_days=QUERY_MAX_AGE_DAYS.get(q["type"], 5),
            keep_limit=per_query_limit,
        )
        stale_removed_total += stale_removed

        if entries:
            results.append({
                "type": q["type"],
                "source": q["source"],
                "symbol": symbol,
                "query": q["query"],
                "entries": entries,
            })

    freshness = {
        "stale_items_removed": stale_removed_total,
        "max_age_days": QUERY_MAX_AGE_DAYS,
        "summary": "Only recent headlines were kept. Older stories were excluded before summarization.",
    }
    return results, freshness


def best_group_score(group: dict[str, Any]) -> float:
    return max((e["score"] for e in group["entries"]), default=0.0)


def select_primary_headline_groups(news_results: list[dict[str, Any]], max_groups: int) -> list[dict[str, Any]]:
    preferred_order = {
        "company_reuters": 0,
        "company_context_reuters": 1,
        "ticker_yahoo": 2,
        "company_yahoo": 3,
        "industry_reuters": 4,
        "sector_reuters": 5,
        "group_industry_reuters": 6,
        "group_sector_reuters": 7,
        "macro_reuters": 8,
    }

    sorted_results = sorted(
        news_results,
        key=lambda x: (
            preferred_order.get(x["type"], 99),
            -best_group_score(x),
        ),
    )
    return sorted_results[:max_groups]


def collect_group_drivers(groups: list[dict[str, Any]]) -> list[str]:
    drivers: list[str] = []
    for group in groups:
        for entry in group["entries"]:
            drivers.extend(entry.get("drivers", []))
    return dedupe_preserve_order(drivers)


def summarize_context_type(groups: list[dict[str, Any]]) -> str:
    types = [g["type"] for g in groups]
    if any(t in types for t in ("company_reuters", "company_context_reuters", "ticker_yahoo", "company_yahoo")):
        return "company_specific"
    if any(t in types for t in ("industry_reuters", "sector_reuters", "group_industry_reuters", "group_sector_reuters")):
        return "sector_specific"
    if "macro_reuters" in types:
        return "macro"
    return "mixed"


def build_per_ticker_context(
    tickers: list[str],
    metadata: dict[str, dict[str, str]],
    news_results: list[dict[str, Any]],
) -> dict[str, Any]:
    output: dict[str, Any] = {}

    for symbol in tickers:
        info = metadata.get(symbol, {})
        ticker_groups = [g for g in news_results if g.get("symbol") == symbol]
        ticker_groups = select_primary_headline_groups(ticker_groups, PER_TICKER_MAX_GROUPS)

        shared_macro = [g for g in news_results if g["type"] == "macro_reuters"][:1]
        if not ticker_groups and shared_macro:
            ticker_groups = shared_macro

        drivers = collect_group_drivers(ticker_groups)
        context_type = summarize_context_type(ticker_groups)

        strongest_headline = None
        if ticker_groups and ticker_groups[0]["entries"]:
            strongest_headline = ticker_groups[0]["entries"][0]["title"]

        output[symbol] = {
            "metadata": info,
            "best_context_type": context_type,
            "drivers": drivers,
            "headline_groups": ticker_groups,
            "strongest_headline": strongest_headline,
            "company_specific_news_found": any(
                g["type"] in ("company_reuters", "company_context_reuters", "ticker_yahoo", "company_yahoo")
                for g in ticker_groups
            ),
            "sector_specific_news_found": any(
                g["type"] in ("industry_reuters", "sector_reuters")
                for g in ticker_groups
            ),
            "macro_news_found": any(g["type"] == "macro_reuters" for g in ticker_groups),
        }

    return output


def infer_shared_drivers(per_ticker_context: dict[str, Any]) -> list[str]:
    driver_counts = Counter()
    total = max(len(per_ticker_context), 1)

    for ctx in per_ticker_context.values():
        for driver in ctx.get("drivers", []):
            driver_counts[driver] += 1

    shared = []
    for driver, count in driver_counts.most_common():
        if count >= max(2, total // 2 + (total % 2 > 0)):
            shared.append(driver)

    return shared


def infer_outlier_tickers(per_ticker_context: dict[str, Any]) -> list[str]:
    type_counts = Counter(ctx.get("best_context_type", "mixed") for ctx in per_ticker_context.values())
    if not type_counts:
        return []

    majority_type = type_counts.most_common(1)[0][0]
    outliers = [
        symbol
        for symbol, ctx in per_ticker_context.items()
        if ctx.get("best_context_type") != majority_type
    ]
    return outliers


def infer_common_sectors(metadata: dict[str, dict[str, str]]) -> list[str]:
    counts = Counter(
        info["sector"]
        for info in metadata.values()
        if info.get("sector")
    )
    return [sector for sector, count in counts.items() if count >= 2]


def infer_market_impact(
    metadata: dict[str, dict[str, str]],
    key_drivers: list[str],
) -> list[str]:
    sectors = dedupe_preserve_order([m["sector"] for m in metadata.values() if m.get("sector")])
    impacts = []

    if sectors:
        impacts.append(f"Sectors represented in the basket: {', '.join(sectors)}.")

    if "Oil and energy market volatility" in key_drivers:
        impacts.append("Energy-sensitive sectors may be reacting to changes in oil and input-cost expectations.")

    if "Geopolitical tensions and conflict-related de-escalation/escalation" in key_drivers:
        impacts.append("Broad sector moves may be be driven by geopolitical headlines rather than company-specific developments.")

    if not impacts:
        impacts.append("The move may reflect a mix of company-specific, sector-specific, and macro developments.")

    return impacts


def build_group_summary(
    tickers: list[str],
    metadata: dict[str, dict[str, str]],
    per_ticker_context: dict[str, Any],
    selected_groups: list[dict[str, Any]],
) -> dict[str, Any]:
    shared_drivers = infer_shared_drivers(per_ticker_context)
    outlier_tickers = infer_outlier_tickers(per_ticker_context)
    common_sectors = infer_common_sectors(metadata)
    all_context_types = [ctx.get("best_context_type", "mixed") for ctx in per_ticker_context.values()]
    dominant_context_type = Counter(all_context_types).most_common(1)[0][0] if all_context_types else "mixed"

    all_group_drivers = collect_group_drivers(selected_groups)
    market_impact = infer_market_impact(metadata, all_group_drivers)

    if not tickers:
        summary = "No tickers were provided, so only broad macro context is available."
    elif len(tickers) == 1:
        symbol = tickers[0]
        ctx = per_ticker_context.get(symbol, {})
        summary = (
            f"{symbol} appears primarily {ctx.get('best_context_type', 'mixed').replace('_', ' ')} "
            "based on the freshest relevant headlines."
        )
    else:
        if shared_drivers:
            summary = (
                f"Most of the basket appears linked to {', '.join(shared_drivers[:2]).lower()}."
            )
        else:
            summary = (
                "The basket does not share one clean common driver; explanations appear mixed across names."
            )

        if outlier_tickers:
            summary += f" Possible outlier tickers: {', '.join(outlier_tickers)}."

    return {
        "summary": summary,
        "shared_drivers": shared_drivers,
        "dominant_context_type": dominant_context_type,
        "outlier_tickers": outlier_tickers,
        "common_sectors": common_sectors,
        "market_impact": market_impact,
        "headline_groups": selected_groups,
    }


def build_macro_summary(
    tickers: list[str],
    group_context: dict[str, Any],
    selected_groups: list[dict[str, Any]],
) -> str:
    if not selected_groups:
        return "No recent relevant Reuters or Yahoo Finance headlines were identified after freshness filtering."

    shared_drivers = group_context.get("shared_drivers", [])
    dominant_context_type = group_context.get("dominant_context_type", "mixed")
    common_sectors = group_context.get("common_sectors", [])

    if len(tickers) <= 1:
        if shared_drivers:
            return (
                "Recent context appears to be driven by "
                f"{', '.join(shared_drivers[:2]).lower()}."
            )
        return (
            f"Recent context appears primarily {dominant_context_type.replace('_', ' ')}."
        )

    if shared_drivers and common_sectors:
        return (
            "Recent market context appears to be driven by "
            f"{', '.join(shared_drivers[:2]).lower()}, with likely spillover into "
            f"{', '.join(common_sectors)} names."
        )

    if shared_drivers:
        return (
            "Recent market context appears to be driven by "
            f"{', '.join(shared_drivers[:2]).lower()}."
        )

    return (
        "Recent relevant headlines were found, but the basket appears to reflect a mixed set of "
        f"{dominant_context_type.replace('_', ' ')} explanations."
    )


def detect_source_mix(selected_groups: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(group["source"] for group in selected_groups)
    return dict(counts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch ticker-aware and group-aware market context from Google News RSS using Reuters and Yahoo Finance queries."
    )
    parser.add_argument(
        "-t",
        "--tickers",
        nargs="+",
        default=[],
        help="One or more ticker symbols, e.g. SOI.PA AKE.PA SOLB.BR AI.PA",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON",
    )
    parser.add_argument(
        "--query-limit",
        type=int,
        default=3,
        help="Max entries kept per query after filtering (default: 3)",
    )
    return parser.parse_args()


def build_output(tickers: list[str], per_query_limit: int) -> dict[str, Any]:
    metadata = get_company_metadata(tickers) if tickers else {}
    queries = build_queries(metadata) if metadata else [{
        "type": "macro_reuters",
        "source": "reuters",
        "symbol": None,
        "company_name": "",
        "query": DEFAULT_MACRO_QUERY,
    }]

    news_results, freshness = build_news_results(
        queries=queries,
        metadata=metadata,
        per_query_limit=per_query_limit,
    )

    selected_groups = select_primary_headline_groups(news_results, GROUP_MAX_GROUPS)
    per_ticker_context = build_per_ticker_context(tickers, metadata, news_results)
    group_context = build_group_summary(tickers, metadata, per_ticker_context, selected_groups)
    macro_summary = build_macro_summary(tickers, group_context, selected_groups)
    source_mix = detect_source_mix(selected_groups)

    return {
        "metadata": metadata,
        "macro_summary": macro_summary,
        "per_ticker_context": per_ticker_context,
        "group_context": group_context,
        "freshness": freshness,
        "source_mix": source_mix,
    }


def print_text(output: dict[str, Any]) -> None:
    print("Macro summary:")
    print(output["macro_summary"])
    print()

    print("Group context:")
    print(json.dumps(output["group_context"], indent=2))
    print()

    print("Per ticker context:")
    print(json.dumps(output["per_ticker_context"], indent=2))
    print()

    print("Freshness:")
    print(output["freshness"]["summary"])
    print(f"Stale items removed: {output['freshness']['stale_items_removed']}")
    print()

    print("Source mix:")
    for source, count in output.get("source_mix", {}).items():
        print(f"- {source}: {count}")


def main() -> None:
    args = parse_args()
    tickers = normalize_tickers(args.tickers)

    try:
        output = build_output(tickers, per_query_limit=args.query_limit)
    except Exception as exc:
        payload = {"error": str(exc)}
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(output, indent=2))
    else:
        print_text(output)


if __name__ == "__main__":
    main()

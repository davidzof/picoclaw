#!/usr/bin/env python3
import argparse
import json
import sys
from typing import Any

import pandas as pd
from yahooquery import Ticker


def fetch_history(ticker: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch historical OHLCV data for a single ticker using yahooquery.
    Returns a cleaned DataFrame indexed by naive datetime with columns:
    Open, High, Low, Close, Volume
    """
    stock = Ticker(ticker)
    hist = stock.history(period=period, interval=interval)

    if hist is None or hist.empty:
        raise ValueError(f"No historical data returned for {ticker}")

    hist = hist.reset_index()

    if "symbol" in hist.columns:
        hist = hist[hist["symbol"] == ticker].copy()

    if hist.empty:
        raise ValueError(f"No rows found for ticker {ticker}")

    required_input_cols = {"date", "open", "high", "low", "close", "volume"}
    missing_input = required_input_cols - set(hist.columns)
    if missing_input:
        raise ValueError(f"Missing source columns for {ticker}: {sorted(missing_input)}")

    hist["date"] = pd.to_datetime(hist["date"], utc=True).dt.tz_convert(None)

    hist.rename(
        columns={
            "date": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        },
        inplace=True,
    )

    hist.set_index("Date", inplace=True)
    hist.sort_index(inplace=True)

    output_cols = ["Open", "High", "Low", "Close", "Volume"]
    hist = hist[output_cols].dropna()

    if hist.empty:
        raise ValueError(f"No usable OHLCV rows remain for {ticker}")

    return hist


def analyze_ticker(ticker: str, hist: pd.DataFrame) -> dict[str, Any]:
    """
    Compute a minimal daily brief from a historical OHLCV DataFrame.
    Requires enough rows to compute 1d, 5d, and 20d-based metrics.
    """
    min_rows = 21
    if len(hist) < min_rows:
        raise ValueError(f"Not enough data for {ticker}: need at least {min_rows} rows, got {len(hist)}")

    close = hist["Close"]
    volume = hist["Volume"]

    latest_close = float(close.iloc[-1])
    prev_close = float(close.iloc[-2])
    close_5d_ago = float(close.iloc[-6])

    ma20 = float(close.tail(20).mean())
    avg_vol20 = float(volume.tail(20).mean())
    latest_vol = float(volume.iloc[-1])

    ret_1d_pct = ((latest_close / prev_close) - 1.0) * 100.0
    ret_5d_pct = ((latest_close / close_5d_ago) - 1.0) * 100.0
    dist_ma20_pct = ((latest_close / ma20) - 1.0) * 100.0 if ma20 else 0.0
    vol_ratio_20d = (latest_vol / avg_vol20) if avg_vol20 else 0.0

    signal = classify_signal(ret_5d_pct, dist_ma20_pct, vol_ratio_20d)

    return {
        "ticker": ticker,
        "last_date": hist.index[-1].strftime("%Y-%m-%d"),
        "close": round(latest_close, 2),
        "ret_1d_pct": round(ret_1d_pct, 2),
        "ret_5d_pct": round(ret_5d_pct, 2),
        "dist_ma20_pct": round(dist_ma20_pct, 2),
        "vol_ratio_20d": round(vol_ratio_20d, 2),
        "signal": signal,
    }


def classify_signal(ret_5d_pct: float, dist_ma20_pct: float, vol_ratio_20d: float) -> str:
    """
    Very simple rule-based label for a first minimal version.
    """
    if ret_5d_pct > 2.0 and dist_ma20_pct > 0.0 and vol_ratio_20d >= 1.0:
        return "bullish"
    if ret_5d_pct < -2.0 and dist_ma20_pct < 0.0 and vol_ratio_20d >= 1.0:
        return "weak"
    if dist_ma20_pct > 3.0:
        return "extended_up"
    if dist_ma20_pct < -3.0:
        return "extended_down"
    return "neutral"


def volume_note(vol_ratio_20d: float) -> str:
    if vol_ratio_20d >= 1.5:
        return "elevated volume"
    if vol_ratio_20d <= 0.7:
        return "light volume"
    return "normal volume"


def summarize_row(row: dict[str, Any]) -> str:
    """
    Human-readable one-line summary for a ticker.
    """
    return (
        f"{row['ticker']}: close {row['close']}, "
        f"1d {signed_pct(row['ret_1d_pct'])}, "
        f"5d {signed_pct(row['ret_5d_pct'])}, "
        f"vs MA20 {signed_pct(row['dist_ma20_pct'])}, "
        f"volume x{row['vol_ratio_20d']} ({volume_note(row['vol_ratio_20d'])}), "
        f"signal={row['signal']}"
    )


def signed_pct(value: float) -> str:
    return f"{value:+.2f}%"


def analyze_many(
    tickers: list[str],
    period: str = "3mo",
    interval: str = "1d",
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """
    Analyze multiple tickers and return:
    - successful results
    - errors
    """
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for ticker in tickers:
        try:
            hist = fetch_history(ticker, period=period, interval=interval)
            analysis = analyze_ticker(ticker, hist)
            results.append(analysis)
        except Exception as exc:
            errors.append({"ticker": ticker, "error": str(exc)})

    return results, errors


def sort_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Sort strongest names first for display.
    """
    signal_rank = {
        "bullish": 0,
        "extended_up": 1,
        "neutral": 2,
        "extended_down": 3,
        "weak": 4,
    }
    return sorted(
        results,
        key=lambda row: (
            signal_rank.get(row["signal"], 99),
            -row["ret_5d_pct"],
            -row["dist_ma20_pct"],
        ),
    )


def print_text_output(results: list[dict[str, Any]], errors: list[dict[str, str]]) -> None:
    if results:
        df = pd.DataFrame(results)
        print(df.to_string(index=False))
        print("\nSummary:")
        for row in results:
            print(f"- {summarize_row(row)}")

    if errors:
        print("\nErrors:", file=sys.stderr)
        for err in errors:
            print(f"- {err['ticker']}: {err['error']}", file=sys.stderr)


def print_json_output(results: list[dict[str, Any]], errors: list[dict[str, str]]) -> None:
    payload = {
        "results": results,
        "errors": errors,
    }
    print(json.dumps(payload, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Minimal daily stock brief using yahooquery."
    )
    parser.add_argument(
        "-t",
        "--tickers",
        nargs="+",
        required=True,
        help="One or more ticker symbols, e.g. AAPL MSFT NVDA AI.PA",
    )
    parser.add_argument(
        "-p",
        "--period",
        default="3mo",
        help="Historical data period (default: 3mo)",
    )
    parser.add_argument(
        "-i",
        "--interval",
        default="1d",
        help="Historical data interval (default: 1d)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON instead of text",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    tickers = [ticker.strip().upper() for ticker in args.tickers if ticker.strip()]
    if not tickers:
        print("No valid tickers supplied.", file=sys.stderr)
        sys.exit(1)

    results, errors = analyze_many(
        tickers=tickers,
        period=args.period,
        interval=args.interval,
    )

    results = sort_results(results)

    if not results and errors:
        if args.json:
            print_json_output([], errors)
        else:
            print_text_output([], errors)
        sys.exit(1)

    if args.json:
        print_json_output(results, errors)
    else:
        print_text_output(results, errors)


if __name__ == "__main__":
    main()

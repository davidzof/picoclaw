# Picoclaw skills to analyze shares

This repo contains the config I use (OpenRouter for the LLM)

## Skills

  * simple skill to give the user's IP address and location
  * Brief - Download and analyze stock information based on their tickers
  * Market Watch - Extract news headlines related to the stock tickers 
  * Analysis - Combine the Brief and Market Watch output to analyze current share prices

## PicoClaw Config

## Example of use

$ picoclaw agent

🦞 You: compare AKE.PA and AI.PA

🦞 Both AKE.PA and AI.PA are currently showing an "extended_up" signal, trading above their 20-day moving averages. AKE.PA emerges as the stronger recent mover with a 3.15% gain over the past five days, while AI.PA has been nearly flat with a -0.02% return. Despite this divergence in short-term performance, both stocks are only moderately extended above their moving averages—5.76% for AKE.PA and 3.63% for AI.PA—and both are trading on extremely light volume, at just 5% of their average 20-day volume. This suggests limited conviction behind the moves.

The broader market context is dominated by oil price volatility driven by US-Iran ceasefire developments. Recent headlines show oil swinging dramatically on ceasefire hopes and concerns, with one report noting a $950 million bet on falling oil prices ahead of the ceasefire announcement, followed by multiple 6-9% price swings as the situation evolved. Energy-sensitive sectors are reacting to these macro developments, with broad sector moves appearing driven by geopolitical events rather than company-specific news.

This macro context directly explains the behavior of both AKE.PA (Aker ASA) and AI.PA (Air Liquide), which are energy-related stocks sensitive to oil prices. The modest gains and notably light volume indicate these moves are primarily macro-driven rather than fueled by individual company catalysts. AKE.PA's slightly stronger five-day performance may reflect greater sensitivity to oil price fluctuations, but both stocks are participating in the same sector-wide trend. The "extended_up" signal fits the pattern: oil price volatility has lifted energy stocks above their moving averages, though the anemic volume suggests traders remain cautious about the sustainability of the ceasefire and its impact on energy markets.

🦞 You: analyse DOW
 
🦞 DOW (Dow Inc.) is currently displaying an "extended_down" signal, trading 6.74% below its 20-day moving average with an 8.33% decline over the past five trading days, indicating a clear short-term downtrend. However, the stock showed a notable 3.29% bounce in the most recent session, offering some relief from the broader decline. Trading volume on this bounce was slightly below average at 79% of the 20-day average, suggesting moderate conviction behind the recovery attempt. The stock appears to be caught in a corrective phase, with the extended_down signal reflecting the recent weakness.

The broader market context is dominated by geopolitical developments surrounding US-Iran ceasefire negotiations, which have triggered extreme oil price volatility. Recent headlines show oil swinging wildly—rising 6% on ceasefire collapse fears, then falling 9% after Iran declared the Strait of Hormuz open and expectations that talks will proceed. Energy-sensitive sectors are reacting sharply to these macro events, with broad-based moves driven by geopolitical factors rather than company-specific news.

This macro context directly explains DOW's behavior as a chemicals company highly sensitive to oil price fluctuations and economic conditions. The five-day decline aligns with periods of oil price uncertainty and potential supply disruptions that increase feedstock costs and economic uncertainty. The recent bounce coincides with headlines about oil falling on improved ceasefire prospects, which would lower input costs and ease economic pressures. The below-average volume on the bounce indicates traders are cautiously responding to macro-driven price swings rather than fundamental catalysts, making DOW's recent action primarily a reflection of energy market volatility during this geopolitical episode.

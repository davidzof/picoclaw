import feedparser

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=oil+war+ceasefire+site:reuters.com&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=markets+stocks+inflation+rates+site:reuters.com&hl=en-US&gl=US&ceid=US:en"
]

KEYWORDS = ["oil", "war", "ceasefire", "inflation", "rates", "energy"]


def fetch_news():
    articles = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:
            articles.append(entry.title)
    return articles


def filter_relevant(articles):
    relevant = []
    for title in articles:
        if any(k.lower() in title.lower() for k in KEYWORDS):
            relevant.append(title)
    return relevant


def build_summary(relevant):
    return {
        "macro_summary": "Recent market moves are driven by geopolitical and energy-related developments.",
        "key_drivers": relevant[:5],
        "market_impact": [
            "Energy-sensitive sectors reacting to oil price changes",
            "Broad sector moves driven by macro events rather than company-specific news"
        ]
    }


def main():
    articles = fetch_news()
    relevant = filter_relevant(articles)
    summary = build_summary(relevant)

    import json
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

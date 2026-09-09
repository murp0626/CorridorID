#!/usr/bin/env python3
"""
Builds an RSS + JSON feed of news related to the FRA Corridor Identification
and Development (Corridor ID) Program, by pulling and merging several
Google News RSS searches (no API key required).

Output:
  docs/feed.xml   - RSS 2.0 feed (subscribe in any reader, or serve via GitHub Pages)
  docs/feed.json  - same items in JSON, handy for other tooling / GitHub Actions

Run manually:
  python scripts/build_feed.py

Intended to run on a schedule via .github/workflows/update-feed.yml
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus

import feedparser
import requests
from feedgen.feed import FeedGenerator

# Edit this list to tune what counts as relevant. Each entry is a separate
# Google News RSS search; results are merged and de-duplicated.
QUERIES = [
    '"Corridor Identification and Development Program"',
    '"Corridor ID Program" rail',
    'FRA "Corridor ID" passenger rail',
    'Federal Railroad Administration corridor rail funding',
]

# Federal Register documents API (official, no key required). Each entry is
# a separate full-text search term against federalregister.gov.
# https://www.federalregister.gov/developers/documentation/api/v1
FEDERAL_REGISTER_TERMS = [
    "Corridor Identification and Development Program",
]
FEDERAL_REGISTER_API = "https://www.federalregister.gov/api/v1/documents.json"

MAX_ITEMS = 75
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs"
FEED_TITLE = "Corridor ID Program News"
FEED_LINK = "https://github.com/"  # replace with your repo/Pages URL after setup
FEED_DESC = "Aggregated news on the FRA Corridor Identification and Development Program for intercity passenger rail."


def google_news_rss_url(query: str) -> str:
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"


def item_id(entry) -> str:
    key = entry.get("link") or entry.get("title", "")
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def fetch_news_items():
    seen = {}
    for q in QUERIES:
        url = google_news_rss_url(q)
        parsed = feedparser.parse(url)
        for entry in parsed.entries:
            uid = item_id(entry)
            if uid in seen:
                continue
            published = entry.get("published_parsed")
            published_dt = (
                datetime(*published[:6], tzinfo=timezone.utc) if published else None
            )
            source = ""
            if "source" in entry and hasattr(entry.source, "title"):
                source = entry.source.title
            seen[uid] = {
                "id": uid,
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", "").strip(),
                "source": source or "Google News",
                "kind": "news",
                "published": published_dt.isoformat() if published_dt else None,
                "matched_query": q,
            }
    return seen


def fetch_federal_register_items():
    seen = {}
    for term in FEDERAL_REGISTER_TERMS:
        params = {
            "conditions[term]": term,
            "order": "newest",
            "per_page": 40,
            "fields[]": [
                "title",
                "abstract",
                "html_url",
                "publication_date",
                "document_number",
                "type",
                "agencies",
            ],
        }
        try:
            resp = requests.get(FEDERAL_REGISTER_API, params=params, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"Federal Register fetch failed for {term!r}: {exc}")
            continue
        for doc in resp.json().get("results", []):
            uid = hashlib.sha256(doc["document_number"].encode("utf-8")).hexdigest()[:16]
            if uid in seen:
                continue
            agencies = ", ".join(a.get("name", "") for a in doc.get("agencies", []))
            pub_date = doc.get("publication_date")  # "YYYY-MM-DD"
            published_dt = (
                datetime.fromisoformat(pub_date).replace(tzinfo=timezone.utc)
                if pub_date
                else None
            )
            seen[uid] = {
                "id": uid,
                "title": doc.get("title", "").strip(),
                "link": doc.get("html_url", "").strip(),
                "source": f"Federal Register — {agencies}" if agencies else "Federal Register",
                "kind": "federal_register",
                "doc_type": doc.get("type"),
                "abstract": doc.get("abstract"),
                "published": published_dt.isoformat() if published_dt else None,
                "matched_query": term,
            }
    return seen


def fetch_items():
    combined = {}
    combined.update(fetch_news_items())
    combined.update(fetch_federal_register_items())
    items = list(combined.values())
    items.sort(key=lambda x: x["published"] or "", reverse=True)
    return items[:MAX_ITEMS]


def write_json(items):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(items),
        "items": items,
    }
    (OUTPUT_DIR / "feed.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_rss(items):
    fg = FeedGenerator()
    fg.title(FEED_TITLE)
    fg.link(href=FEED_LINK, rel="alternate")
    fg.description(FEED_DESC)
    fg.language("en")

    for it in items:
        fe = fg.add_entry()
        fe.id(it["link"] or it["id"])
        fe.title(it["title"])
        if it["link"]:
            fe.link(href=it["link"])
        desc = it.get("abstract") or it["source"] or ""
        fe.description(desc)
        fe.category(term=it.get("kind", "news"))
        if it["published"]:
            fe.pubDate(it["published"])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fg.rss_file(str(OUTPUT_DIR / "feed.xml"))


def main():
    items = fetch_items()
    write_json(items)
    write_rss(items)
    print(f"Wrote {len(items)} items to {OUTPUT_DIR}/feed.xml and feed.json")


if __name__ == "__main__":
    main()

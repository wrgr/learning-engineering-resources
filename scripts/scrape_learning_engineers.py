"""Scrapes GitHub API and DuckDuckGo for people using 'Learning Engineer' as a job title.

Excludes any variant containing 'machine learning'. Appends new records to
data/people.jsonl. Run: python3 scripts/scrape_learning_engineers.py [--github] [--web]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUTPUT_PATH = DATA_DIR / "people.jsonl"

GITHUB_API_BASE = "https://api.github.com"
DDG_HTML_URL = "https://html.duckduckgo.com/html/"

# Unauthenticated GitHub search: 10 req/min. With token: 5000/hr.
GITHUB_SLEEP_SEC = 6.5
WEB_SLEEP_SEC = 4.0

_ML_EXCLUDE = re.compile(r"\bmachine\s+learning\b", re.IGNORECASE)
_LE_INCLUDE = re.compile(r"\blearning\s+engineer", re.IGNORECASE)

# Heuristic patterns: "Name — Learning Engineer at Org" or "Name, Learning Engineer"
_SNIPPET_NAME_TITLE = [
    re.compile(
        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*[-–|]\s*Learning Engineer"
        r"(?:\s+(?:at|@|,)\s+([^|\-\n]{3,50}))?",
        re.IGNORECASE,
    ),
    re.compile(
        r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+),\s*Learning Engineer"
        r"(?:\s+(?:at|@)\s+([^|\-\n]{3,50}))?",
        re.IGNORECASE,
    ),
]

DDG_QUERIES = [
    '"learning engineer" -"machine learning" conference speaker biography',
    '"learning engineer" -"machine learning" ieee icicle member',
    '"learning engineer" -"machine learning" edtech team about',
    '"learning engineer" -"machine learning" "I am a" OR "I\'m a"',
    '"senior learning engineer" -"machine learning"',
]


# ---------------------------------------------------------------------------
# Title filtering
# ---------------------------------------------------------------------------

def is_le_title(text: str) -> bool:
    """Return True if text contains 'learning engineer' but not 'machine learning'."""
    return bool(_LE_INCLUDE.search(text)) and not bool(_ML_EXCLUDE.search(text))


def extract_title_phrase(text: str) -> str:
    """Pull a short title phrase around the 'learning engineer' match."""
    match = _LE_INCLUDE.search(text)
    if not match:
        return "Learning Engineer"
    start = max(0, match.start() - 15)
    end = min(len(text), match.end() + 25)
    phrase = text[start:end].strip().split("\n")[0]
    return re.sub(r"\s+", " ", phrase).strip()


# ---------------------------------------------------------------------------
# Record I/O and ID generation
# ---------------------------------------------------------------------------

def load_existing_keys(path: Path) -> set[str]:
    """Return (name|org) dedup keys from an existing people.jsonl."""
    if not path.is_file():
        return set()
    keys: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            keys.add(_dedup_key(rec.get("name", ""), rec.get("organization", "")))
        except json.JSONDecodeError:
            continue
    return keys


def _dedup_key(name: str, org: str) -> str:
    """Produce a lowercase dedup key."""
    return f"{name.strip().lower()}|{org.strip().lower()}"


def next_person_id(path: Path) -> str:
    """Return the next LP-NNN ID based on line count in existing file."""
    if not path.is_file():
        return "LP-001"
    count = sum(1 for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip())
    return f"LP-{count + 1:03d}"


def append_record(record: dict, path: Path) -> None:
    """Append one JSON record to the JSONL output file."""
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def fetch_url(
    url: str,
    headers: Optional[dict[str, str]] = None,
    retries: int = 3,
) -> str:
    """Fetch URL and return response body; retries on transient errors."""
    req = urllib.request.Request(url, headers=headers or {})
    last_exc: Exception = RuntimeError("no attempts")
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code in (429, 403):
                time.sleep(12 * (2 ** attempt))
            else:
                time.sleep(2 ** attempt)
        except Exception as exc:
            last_exc = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed {url} after {retries} attempts: {last_exc}") from last_exc


def github_headers() -> dict[str, str]:
    """Return GitHub API headers, adding Bearer token if GITHUB_TOKEN is set."""
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "LE-People-Scraper/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN", "")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# ---------------------------------------------------------------------------
# GitHub source
# ---------------------------------------------------------------------------

def fetch_github_users(limit: int = 300) -> list[dict]:
    """Search GitHub for users whose bio contains 'learning engineer'."""
    results: list[dict] = []
    page = 1
    per_page = 30  # GitHub caps user search at 30/page
    hdrs = github_headers()
    while len(results) < limit:
        params = urllib.parse.urlencode(
            {"q": "learning engineer in:bio", "per_page": per_page, "page": page}
        )
        url = f"{GITHUB_API_BASE}/search/users?{params}"
        try:
            body = fetch_url(url, headers=hdrs)
        except RuntimeError as exc:
            print(f"  [github] search failed: {exc}")
            break
        data = json.loads(body)
        items = data.get("items", [])
        if not items:
            break
        results.extend(items)
        if len(items) < per_page:
            break
        page += 1
        time.sleep(GITHUB_SLEEP_SEC)
    return results[:limit]


def fetch_github_user_detail(login: str) -> dict:
    """Fetch a single GitHub user's full profile JSON."""
    url = f"{GITHUB_API_BASE}/users/{login}"
    body = fetch_url(url, headers=github_headers())
    return json.loads(body)


def parse_github_user(raw: dict, today: str) -> Optional[dict]:
    """Convert a GitHub profile dict to a person record, or None if title doesn't qualify."""
    bio = (raw.get("bio") or "").strip()
    company = re.sub(r"^@", "", (raw.get("company") or "").strip())
    name = (raw.get("name") or raw.get("login") or "").strip()
    if not name or not is_le_title(bio):
        return None
    blog = (raw.get("blog") or "").strip()
    profile_urls = [u for u in [raw.get("html_url", ""), blog] if u]
    return {
        "record_type": "learning_engineer_person",
        "name": name,
        "title_as_found": extract_title_phrase(bio),
        "organization": company,
        "source_url": raw.get("html_url", ""),
        "source_type": "github_api",
        "profile_urls": profile_urls,
        "location": (raw.get("location") or "").strip(),
        "bio_snippet": bio[:300],
        "date_collected": today,
        "verified": False,
        "notes": "",
    }


def run_github_source(
    existing_keys: set[str], today: str, limit: int
) -> list[dict]:
    """Fetch GitHub users and return new person records not already in the database."""
    print(f"[github] Searching for up to {limit} users with 'learning engineer' in bio…")
    search_results = fetch_github_users(limit=limit)
    print(f"[github] {len(search_results)} candidate profiles found")
    records: list[dict] = []
    for item in search_results:
        login = item.get("login", "")
        try:
            detail = fetch_github_user_detail(login)
            time.sleep(GITHUB_SLEEP_SEC)
        except RuntimeError as exc:
            print(f"  [github] skipping {login}: {exc}")
            continue
        record = parse_github_user(detail, today)
        if record is None:
            continue
        key = _dedup_key(record["name"], record["organization"])
        if key in existing_keys:
            print(f"  [github] duplicate skipped: {record['name']}")
            continue
        existing_keys.add(key)
        records.append(record)
        print(f"  [github] + {record['name']} ({record['organization']})")
    return records


# ---------------------------------------------------------------------------
# DuckDuckGo HTML source
# ---------------------------------------------------------------------------

class _DDGParser(HTMLParser):
    """Minimal HTML parser for DuckDuckGo result snippets and titles."""

    def __init__(self) -> None:
        super().__init__()
        self.results: list[dict] = []
        self._in_a = False
        self._in_snippet = False
        self._cur_title = ""
        self._cur_url = ""
        self._cur_snippet: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Track entry into result title anchors and snippet divs."""
        attr = dict(attrs)
        cls = attr.get("class") or ""
        if tag == "a" and "result__a" in cls:
            self._in_a = True
            self._cur_url = attr.get("href") or ""
            self._cur_title = ""
        elif tag == "div" and "result__snippet" in cls:
            self._in_snippet = True
            self._cur_snippet = []

    def handle_data(self, data: str) -> None:
        """Accumulate text inside tracked elements."""
        if self._in_a:
            self._cur_title += data
        elif self._in_snippet:
            self._cur_snippet.append(data)

    def handle_endtag(self, tag: str) -> None:
        """Flush completed result entries."""
        if tag == "a" and self._in_a:
            self._in_a = False
        elif tag == "div" and self._in_snippet:
            self._in_snippet = False
            snippet_text = "".join(self._cur_snippet).strip()
            if self._cur_title or snippet_text:
                self.results.append(
                    {
                        "title": self._cur_title.strip(),
                        "url": self._cur_url,
                        "snippet": snippet_text,
                    }
                )
            self._cur_title = ""
            self._cur_url = ""


def fetch_ddg_results(query: str) -> list[dict]:
    """Run a DuckDuckGo HTML search and return parsed result dicts."""
    params = urllib.parse.urlencode({"q": query, "kl": "us-en"})
    url = f"{DDG_HTML_URL}?{params}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; LE-People-Scraper/1.0; "
            "+https://github.com/wrgr/learning-engineering-resources)"
        ),
        "Accept": "text/html",
    }
    try:
        html = fetch_url(url, headers=headers)
    except RuntimeError as exc:
        print(f"  [web] DDG request failed: {exc}")
        return []
    parser = _DDGParser()
    parser.feed(html)
    return parser.results


def parse_snippet_for_person(result: dict, today: str) -> Optional[dict]:
    """Attempt to extract a person record from a DDG search result snippet."""
    combined = f"{result.get('title', '')} {result.get('snippet', '')}".strip()
    if not is_le_title(combined):
        return None
    name, org = "", ""
    for pattern in _SNIPPET_NAME_TITLE:
        m = pattern.search(combined)
        if m:
            name = m.group(1).strip()
            org = (m.group(2) or "").strip().rstrip(".,;")
            break
    if not name:
        return None
    return {
        "record_type": "learning_engineer_person",
        "name": name,
        "title_as_found": extract_title_phrase(combined),
        "organization": org,
        "source_url": result.get("url", ""),
        "source_type": "web_search_snippet",
        "profile_urls": [result.get("url", "")] if result.get("url") else [],
        "location": "",
        "bio_snippet": combined[:300],
        "date_collected": today,
        "verified": False,
        "notes": "Needs manual verification — extracted from search snippet.",
    }


def run_web_source(existing_keys: set[str], today: str) -> list[dict]:
    """Run DDG queries and return new person records extracted from snippets."""
    records: list[dict] = []
    for query in DDG_QUERIES:
        print(f"[web] Query: {query}")
        results = fetch_ddg_results(query)
        print(f"  {len(results)} results")
        for result in results:
            record = parse_snippet_for_person(result, today)
            if record is None:
                continue
            key = _dedup_key(record["name"], record["organization"])
            if key in existing_keys:
                continue
            existing_keys.add(key)
            records.append(record)
            print(f"  [web] + {record['name']} ({record['organization']})")
        time.sleep(WEB_SLEEP_SEC)
    return records


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Parse args, run enabled sources, and append new records to people.jsonl."""
    parser = argparse.ArgumentParser(
        description="Scrape for people with 'Learning Engineer' in their title."
    )
    parser.add_argument(
        "--github", action="store_true", default=False, help="Run GitHub API source"
    )
    parser.add_argument(
        "--web", action="store_true", default=False, help="Run DuckDuckGo web search source"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=300,
        help="Max GitHub user profiles to inspect (default 300)",
    )
    args = parser.parse_args()

    # Default: run both sources if neither flag given
    run_github = args.github or (not args.github and not args.web)
    run_web = args.web or (not args.github and not args.web)

    today = date.today().isoformat()
    existing_keys = load_existing_keys(OUTPUT_PATH)
    print(f"Existing records: {len(existing_keys)}  |  Output: {OUTPUT_PATH}")

    all_new: list[dict] = []

    if run_github:
        all_new.extend(run_github_source(existing_keys, today, limit=args.limit))

    if run_web:
        all_new.extend(run_web_source(existing_keys, today))

    for record in all_new:
        record["person_id"] = next_person_id(OUTPUT_PATH)
        append_record(record, OUTPUT_PATH)

    print(f"\nDone. {len(all_new)} new record(s) written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

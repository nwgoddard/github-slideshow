#!/usr/bin/env python3
"""Fetch free survey data from realtyrates.com and save as normalized JSON."""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

SURVEYS = {
    "commercial_rates": "https://www.realtyrates.com/commercial-mortgage-rates.html",
    "indices": "https://www.realtyrates.com/indices.html",
    "developer_survey": "https://www.realtyrates.com/ds-property-types.html",
}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO_ROOT, "_data", "realtyrates")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def fetch_page(url: str, retries: int = 4) -> BeautifulSoup:
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "lxml")
        except requests.RequestException as exc:
            if attempt == retries - 1:
                raise
            wait = 2 ** attempt
            print(f"  Attempt {attempt + 1} failed: {exc}. Retrying in {wait}s…")
            time.sleep(wait)


# ---------------------------------------------------------------------------
# Generic table parser
# ---------------------------------------------------------------------------

def parse_rate(text: str) -> float | None:
    """Extract a float from strings like '4.75%', '4.75 - 5.25%', '$4.75'."""
    text = text.strip().replace(",", "")
    nums = re.findall(r"\d+\.?\d*", text)
    if not nums:
        return None
    values = [float(n) for n in nums]
    return sum(values) / len(values)  # average of range if present


def parse_rate_range(text: str) -> tuple[float | None, float | None]:
    text = text.strip().replace(",", "")
    nums = re.findall(r"\d+\.?\d*", text)
    if len(nums) >= 2:
        return float(nums[0]), float(nums[-1])
    if len(nums) == 1:
        v = float(nums[0])
        return v, v
    return None, None


def extract_tables(soup: BeautifulSoup) -> list[dict]:
    """Return all data tables as list of {title, headers, rows}."""
    results = []
    for table in soup.find_all("table"):
        caption = table.find("caption")
        title = caption.get_text(strip=True) if caption else None

        all_rows = table.find_all("tr")
        if not all_rows:
            continue

        headers: list[str] = []
        rows: list[dict | list] = []

        for i, tr in enumerate(all_rows):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all(["th", "td"])]
            if not cells:
                continue
            th_count = len(tr.find_all("th"))
            if i == 0 or th_count == len(cells):
                headers = cells
            else:
                if headers and len(cells) == len(headers):
                    rows.append(dict(zip(headers, cells)))
                else:
                    rows.append(cells)

        if rows:
            results.append({"title": title, "headers": headers, "rows": rows})
    return results


# ---------------------------------------------------------------------------
# Page-specific normalizers
# ---------------------------------------------------------------------------

def normalize_commercial_rates(soup: BeautifulSoup, fetched_at: str) -> dict:
    """Extract cap rates and mortgage rates by property type."""
    tables = extract_tables(soup)
    property_types: list[dict] = []

    # Detect the survey quarter from page text
    quarter = None
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "td", "th"]):
        text = tag.get_text(strip=True)
        m = re.search(r"Q[1-4]\s*20\d{2}", text, re.I)
        if m:
            quarter = m.group(0).replace(" ", "")
            break

    for tbl in tables:
        for row in tbl["rows"]:
            if not isinstance(row, dict):
                continue
            # Identify property-type column (first non-empty non-numeric cell)
            name = None
            for k, v in row.items():
                if v and not re.match(r"^[\d\.\-\%\s]+$", v):
                    name = v
                    break
            if not name:
                continue

            entry: dict = {"name": name}

            for k, v in row.items():
                kl = k.lower()
                if "cap" in kl and ("low" in kl or "min" in kl):
                    lo, _ = parse_rate_range(v)
                    entry["cap_rate_low"] = lo
                elif "cap" in kl and ("high" in kl or "max" in kl):
                    _, hi = parse_rate_range(v)
                    entry["cap_rate_high"] = hi
                elif "cap" in kl and "avg" in kl:
                    entry["cap_rate_avg"] = parse_rate(v)
                elif ("interest" in kl or "rate" in kl or "mort" in kl) and "low" in kl:
                    lo, _ = parse_rate_range(v)
                    entry["interest_rate_low"] = lo
                elif ("interest" in kl or "rate" in kl or "mort" in kl) and "high" in kl:
                    _, hi = parse_rate_range(v)
                    entry["interest_rate_high"] = hi
                elif ("interest" in kl or "rate" in kl or "mort" in kl) and "avg" in kl:
                    entry["interest_rate_avg"] = parse_rate(v)
                elif "ltv" in kl or "loan-to" in kl:
                    entry["ltv_max"] = parse_rate(v)
                elif "amort" in kl:
                    entry["amortization"] = parse_rate(v)

            # Compute averages where missing
            for metric in ("cap_rate", "interest_rate"):
                lo_k, hi_k, avg_k = f"{metric}_low", f"{metric}_high", f"{metric}_avg"
                if avg_k not in entry and lo_k in entry and hi_k in entry:
                    lo, hi = entry[lo_k], entry[hi_k]
                    if lo is not None and hi is not None:
                        entry[avg_k] = round((lo + hi) / 2, 4)

            if len(entry) > 1:
                property_types.append(entry)

    return {
        "fetched_at": fetched_at,
        "quarter": quarter,
        "source": "RealtyRates.com Commercial Mortgage Rate Survey",
        "property_types": property_types,
    }


def normalize_indices(soup: BeautifulSoup, fetched_at: str) -> dict:
    """Extract financial benchmark indices."""
    tables = extract_tables(soup)
    indices: list[dict] = []

    for tbl in tables:
        for row in tbl["rows"]:
            if not isinstance(row, dict):
                continue
            name = None
            for k, v in row.items():
                if v and not re.match(r"^[\d\.\-\%\s]+$", v):
                    name = v
                    break
            if not name:
                continue
            entry: dict = {"name": name}
            for k, v in row.items():
                kl = k.lower()
                if "current" in kl or "rate" in kl or "value" in kl:
                    entry["value"] = parse_rate(v)
                elif "prev" in kl or "prior" in kl or "last" in kl:
                    entry["previous"] = parse_rate(v)
            if "value" in entry:
                indices.append(entry)

    return {
        "fetched_at": fetched_at,
        "source": "RealtyRates.com Financial Indices",
        "indices": indices,
    }


def normalize_developer_survey(soup: BeautifulSoup, fetched_at: str) -> dict:
    """Extract developer survey data (subdivisions, PUDs, condos, etc.)."""
    tables = extract_tables(soup)
    categories: list[dict] = []
    quarter = None

    for tag in soup.find_all(["h1", "h2", "h3", "h4", "p", "td", "th"]):
        text = tag.get_text(strip=True)
        m = re.search(r"Q[1-4]\s*20\d{2}", text, re.I)
        if m:
            quarter = m.group(0).replace(" ", "")
            break

    for tbl in tables:
        cat_name = tbl.get("title") or "Unknown"
        metrics: list[dict] = []
        for row in tbl["rows"]:
            if not isinstance(row, dict):
                continue
            values = list(row.values())
            if len(values) < 2:
                continue
            metric_name = values[0]
            if not metric_name or re.match(r"^[\d\.\-\%\s]+$", metric_name):
                continue
            entry: dict = {"name": metric_name}
            numerics = [parse_rate(v) for v in values[1:] if parse_rate(v) is not None]
            if len(numerics) >= 2:
                entry["low"] = min(numerics)
                entry["high"] = max(numerics)
                entry["avg"] = round(sum(numerics) / len(numerics), 4)
            elif len(numerics) == 1:
                entry["avg"] = numerics[0]
            if len(entry) > 1:
                metrics.append(entry)
        if metrics:
            categories.append({"name": cat_name, "metrics": metrics})

    return {
        "fetched_at": fetched_at,
        "quarter": quarter,
        "source": "RealtyRates.com Developer Survey",
        "categories": categories,
    }


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def save(name: str, data: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f"{name}.json")
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)
    print(f"  Saved {path}")


def update_history(all_surveys: dict, fetched_at: str) -> None:
    history_path = os.path.join(DATA_DIR, "history.json")
    try:
        with open(history_path) as fh:
            history = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []

    snapshot: dict = {"fetched_at": fetched_at, "surveys": {}}
    for name, data in all_surveys.items():
        if data.get("property_types"):
            # Store avg cap/interest rates per property type for trend tracking
            snapshot["surveys"][name] = {
                "quarter": data.get("quarter"),
                "property_types": [
                    {
                        "name": pt["name"],
                        "cap_rate_avg": pt.get("cap_rate_avg"),
                        "interest_rate_avg": pt.get("interest_rate_avg"),
                    }
                    for pt in data.get("property_types", [])
                ],
            }
    history.append(snapshot)
    history = history[-16:]  # keep ~4 years of quarterly data

    with open(history_path, "w") as fh:
        json.dump(history, fh, indent=2)
    print(f"  Updated {history_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

NORMALIZERS = {
    "commercial_rates": normalize_commercial_rates,
    "indices": normalize_indices,
    "developer_survey": normalize_developer_survey,
}


def main() -> int:
    fetched_at = datetime.now(timezone.utc).isoformat()
    results: dict[str, dict] = {}
    errors: list[str] = []

    for name, url in SURVEYS.items():
        print(f"\nFetching {name} …")
        try:
            soup = fetch_page(url)
            normalize = NORMALIZERS[name]
            data = normalize(soup, fetched_at)
            save(name, data)
            results[name] = data
            print(f"  OK ({len(data.get('property_types', data.get('indices', data.get('categories', []))))} records)")
            time.sleep(2)
        except Exception as exc:
            print(f"  ERROR: {exc}", file=sys.stderr)
            errors.append(f"{name}: {exc}")

    if results:
        update_history(results, fetched_at)

    metadata = {
        "last_updated": fetched_at,
        "data_source": "RealtyRates.com",
        "surveys": {
            name: {"status": "ok" if name not in [e.split(":")[0] for e in errors] else "error"}
            for name in SURVEYS
        },
        "is_stub": False,
    }
    save("metadata", metadata)

    if errors:
        print(f"\n{len(errors)} survey(s) failed:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"\nAll {len(SURVEYS)} surveys fetched successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

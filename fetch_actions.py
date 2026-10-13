"""Download NSE corporate actions (stocks and ETFs) into data/corporate_actions.csv.

    python fetch_actions.py 2026-07-01 2026-10-09

NSE's API refuses requests without the cookies its listing page sets, so the
page is fetched first in the same session. The subject line is free text; this
script classifies it and pulls out the two numbers a split or bonus needs.
Turning those numbers into an adjustment factor is left to the SQL.
"""
import csv
import gzip
import http.cookiejar
import json
import re
import sys
import urllib.request
from datetime import date, datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "corporate_actions.csv"
PAGE = "https://www.nseindia.com/companies-listing/corporate-filings-actions"
API = "https://www.nseindia.com/api/corporates-corporateActions?index={}&from_date={}&to_date={}"
# Stocks are in "equities". ETFs trade in the same EQ series but their actions
# (unit splits included) are only listed in "mf".
FEEDS = ("equities", "mf")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "*/*",
    "Referer": PAGE,
}

# "Face Value Split (Sub-Division) - From Rs 10/- Per Share To Re 1/- Per Share"
SPLIT = re.compile(r"^Face Value Split.*From R[se]\.? ?([\d.]+).*To R[se]\.? ?([\d.]+)", re.I)
# "Bonus 2:1" means 2 new shares for every 1 held. Anchored, so the
# "Scheme Of Arrangement - Bonus Ncrps 4:1" preference-share issues stay out.
BONUS = re.compile(r"^Bonus (\d+):(\d+)", re.I)


def classify(subject: str):
    """Return (kind, num_a, num_b). For a split a/b are the old and new face
    value; for a bonus they are the x and y of 'x:y'. Other kinds have none."""
    if m := SPLIT.match(subject):
        return "split", float(m[1]), float(m[2])
    if m := BONUS.match(subject):
        return "bonus", float(m[1]), float(m[2])
    s = subject.lower()
    for kind in ("demerger", "rights", "dividend"):
        if kind in s:
            return kind, None, None
    return "other", None, None


def fetch(start: date, end: date) -> list[tuple[str, dict]]:
    """Return (feed, action) pairs from both feeds NSE splits listings into."""
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def get(url: str) -> bytes:
        r = opener.open(urllib.request.Request(url, headers=HEADERS), timeout=30)
        body = r.read()
        return gzip.decompress(body) if r.headers.get("Content-Encoding") == "gzip" else body

    get(PAGE)
    fmt = "%d-%m-%Y"
    out = []
    for feed in FEEDS:
        url = API.format(feed, start.strftime(fmt), end.strftime(fmt))
        out += [(feed, r) for r in json.loads(get(url))]
    return out


def main() -> None:
    start, end = (date.fromisoformat(a) for a in sys.argv[1:3])
    rows, seen, dupes = [], set(), 0
    for feed, r in fetch(start, end):
        # The mf feed lists every action twice. A split applied twice would
        # square its factor, so keep the first copy only.
        key = (r["symbol"], r["exDate"], r["subject"])
        if key in seen:
            dupes += 1
            continue
        seen.add(key)
        kind, a, b = classify(r["subject"])
        rows.append({
            "feed": feed,
            "symbol": r["symbol"],
            "series": r["series"],
            "isin": r["isin"],
            "ex_date": datetime.strptime(r["exDate"], "%d-%b-%Y").date().isoformat(),
            "kind": kind,
            "num_a": a,
            "num_b": b,
            "subject": r["subject"],
        })
    rows.sort(key=lambda r: (r["ex_date"], r["symbol"], r["subject"]))
    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} actions ({dupes} duplicates dropped) -> {OUT}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Find publications on OpenAlex and Google Scholar that are not yet in _data/publications.yml.

OpenAlex (linked to your ORCID) is the main source: it has DOIs and full author
names. Your public Google Scholar profile is checked too. Papers that are on
Scholar but not OpenAlex are looked up on Crossref by title, and otherwise added
with Scholar's (abbreviated) details. Scholar has no API and sometimes blocks
automated requests; when that happens the sync simply uses OpenAlex alone.

New works are appended to the YAML file with `selected: false` so they show up
in the full list but not on the homepage. Review the diff before publishing:
OpenAlex occasionally attributes someone else's paper to you, and conference
papers are often listed under "Lecture Notes in Computer Science" instead of
the conference name.

Usage:
    python3 scripts/sync_publications.py            # append new works
    python3 scripts/sync_publications.py --dry-run  # print them instead
    python3 scripts/sync_publications.py --since 2020
    python3 scripts/sync_publications.py --no-scholar  # OpenAlex only

Standard library only, so it runs anywhere Python 3.8+ is available.
"""

import argparse
import datetime
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ORCID = "0000-0002-6995-2312"
SCHOLAR_ID = "8jHbkMcAAAAJ"
# Only keep works where your authorship lists one of these institutions.
# This filters out most OpenAlex mis-attributions.
AFFILIATIONS = ("Harvard", "Daegu Gyeongbuk", "DGIST", "Chonbuk", "Jeonbuk")
SKIP_TYPES = {"dataset", "paratext", "erratum", "peer-review", "editorial", "letter", "other"}

ROOT = Path(__file__).resolve().parent.parent
PUBS_FILE = ROOT / "_data" / "publications.yml"
IGNORE_FILE = Path(__file__).resolve().parent / "publications_ignore.txt"

# Journal/proceedings name -> short label shown on the badge.
SHORT_VENUES = {
    "IEEE Transactions on Medical Imaging": "IEEE TMI",
    "IEEE Journal of Biomedical and Health Informatics": "IEEE JBHI",
    "IEEE Transactions on Neural Networks and Learning Systems": "IEEE TNNLS",
    "Medical Image Analysis": "MedIA",
    "Pattern Recognition": "Pattern Recognition",
    "Neural Networks": "Neural Networks",
    "Information Fusion": "Information Fusion",
    "Expert Systems with Applications": "ESWA",
    "Computers in Biology and Medicine": "CIBM",
    "Proceedings of the AAAI Conference on Artificial Intelligence": "AAAI",
    "Signal Transduction and Targeted Therapy": "STTT",
    "Frontiers in Medicine": "Front. Med.",
    "arXiv (Cornell University)": "arXiv",
}
TYPE_MAP = {"article": "journal", "review": "journal", "preprint": "preprint",
            "conference-paper": "conference", "proceedings-article": "conference",
            "book-chapter": "conference"}
CROSSREF_TYPES = {"journal-article": "journal", "proceedings-article": "conference",
                  "book-chapter": "conference", "posted-content": "preprint"}
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")


def norm(title):
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())


def fetch_works(since):
    works, cursor = [], "*"
    while cursor:
        params = urllib.parse.urlencode({
            "filter": f"author.orcid:{ORCID},from_publication_date:{since}-01-01",
            "per-page": 200, "cursor": cursor,
            "select": "id,title,publication_date,publication_year,type,doi,primary_location,authorships",
        })
        with urllib.request.urlopen(f"https://api.openalex.org/works?{params}", timeout=30) as r:
            data = json.load(r)
        works += data["results"]
        cursor = data["meta"].get("next_cursor") if data["results"] else None
    return works


def my_institutions(work):
    for a in work["authorships"]:
        if (a["author"].get("orcid") or "").endswith(ORCID):
            return [i["display_name"] for i in a["institutions"]]
    return []


def existing_keys():
    text = PUBS_FILE.read_text() if PUBS_FILE.exists() else ""
    titles = {norm(t) for t in re.findall(r'^\s*-?\s*title:\s*"(.*)"\s*$', text, re.M)}
    dois = {d.lower() for d in re.findall(r'^\s*doi:\s*"?([^"\s]+)"?\s*$', text, re.M)}
    ids = set(re.findall(r'^\s*openalex:\s*"?(W\d+)"?\s*$', text, re.M))
    return titles, dois, ids


def ignored():
    if not IGNORE_FILE.exists():
        return set()
    lines = [l.split("#")[0].strip() for l in IGNORE_FILE.read_text().splitlines()]
    return {l.lower() for l in lines if l} | {norm(l) for l in lines if l}


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def crossref_event(doi):
    """Conference acronym/name for a DOI (Springer LNCS chapters list the event, not the book)."""
    try:
        with urllib.request.urlopen(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}", timeout=20) as r:
            msg = json.load(r)["message"]
    except Exception:
        return None, None
    event = msg.get("event") or {}
    facts = {a.get("name"): a.get("value") for a in msg.get("assertion", [])}
    book = (msg.get("container-title") or [""])[-1]
    # Proceedings titles look like "Medical Image Computing ... – MICCAI 2020".
    in_title = re.search(r"[–-]\s*([A-Z][A-Za-z]{2,})\s+\d{4}$", book)
    name = facts.get("conference_name") or event.get("name") or book or None
    # "... Intelligent Robots and Systems (IROS)" -> "IROS"
    in_name = re.search(r"\(([A-Z][A-Za-z]{2,})\)\s*$", name or "")
    return (facts.get("conference_acronym") or event.get("acronym")
            or (in_title and in_title.group(1)) or (in_name and in_name.group(1)), name)


def fetch_scholar():
    """Rows (title, authors, venue, year) from the public Google Scholar profile, newest first.

    Returns [] when Scholar is unreachable or asks for a CAPTCHA, which happens
    fairly often from cloud servers such as GitHub Actions.
    """
    url = (f"https://scholar.google.com/citations?user={SCHOLAR_ID}&hl=en"
           "&view_op=list_works&sortby=pubdate&cstart=0&pagesize=100")
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, "Accept-Language": "en-US,en;q=0.9"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            page = r.read().decode("utf-8", "replace")
    except Exception as e:
        print(f"Google Scholar unavailable ({e}); using OpenAlex only.", file=sys.stderr)
        return []
    if "gsc_a_tr" not in page:
        print("Google Scholar blocked the request (CAPTCHA); using OpenAlex only.", file=sys.stderr)
        return []

    def clean(fragment):
        return html.unescape(re.sub(r"<.*?>", "", fragment)).strip()

    rows = []
    for row in re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', page, re.S):
        title = re.search(r'class="gsc_a_at">(.*?)</a>', row, re.S)
        grays = re.findall(r'<div class="gs_gray">(.*?)</div>', row, re.S)
        year = re.search(r'gsc_a_h gsc_a_hc gs_ibl">(\d{4})<', row)
        if not title:
            continue
        rows.append({
            "title": clean(title.group(1)),
            "authors": clean(grays[0]) if grays else "",
            "venue": clean(re.sub(r'<span class="gs_oph">.*?</span>', "", grays[1])) if len(grays) > 1 else "",
            "year": int(year.group(1)) if year else None,
        })
    print(f"Google Scholar: {len(rows)} works on profile.", file=sys.stderr)
    return rows


def crossref_by_title(title):
    """Crossref record whose title matches exactly (ignoring case/punctuation), or None."""
    params = urllib.parse.urlencode({"query.bibliographic": title, "rows": 5})
    try:
        with urllib.request.urlopen(f"https://api.crossref.org/works?{params}", timeout=20) as r:
            items = json.load(r)["message"]["items"]
    except Exception:
        return None
    return next((it for it in items if norm((it.get("title") or [""])[0]) == norm(title)), None)


def venue_labels(src, doi, year, kind):
    """(badge label, full venue name, type) for a journal or proceedings name."""
    short, full = SHORT_VENUES.get(src, src), src
    if "arxiv" in src.lower():
        return "arXiv", "arXiv preprint", "preprint"
    # "2022 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)" -> "CVPR 2022"
    acr = re.search(r"\(([A-Z][A-Za-z]{2,})\)\s*$", src)
    if src not in SHORT_VENUES and acr:
        short, kind = f"{acr.group(1)} {year}", "conference"
    if doi and (not src or "lecture notes" in src.lower() or "communications in computer" in src.lower()):
        acronym, name = crossref_event(doi)
        if acronym or name:
            label = acronym or name
            short = label if label.endswith(str(year)) else f"{label} {year}"
            full, kind = name or full, "conference"
    return short, full, kind


def entry_yaml(title, authors, short, full, year, date, kind, doi, source_line, note=None):
    lines = [f"# {note}"] if note else []
    lines += [f"- title: {q(title)}", f"  authors: [{', '.join(q(a) for a in authors)}]"]
    lines.append(f"  venue: {q(short)}" if short else '  venue: ""  # TODO: add venue')
    lines += [f"  venue_full: {q(full)}", f"  year: {year}", f"  date: {date}", f"  type: {kind}"]
    if doi:
        lines += [f"  doi: {q(doi)}", "  links:", f"    paper: {q('https://doi.org/' + doi)}"]
    lines += ["  selected: false", "  topics: []", source_line]
    return "\n".join(lines)


def to_yaml(w):
    """YAML entry for an OpenAlex work."""
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    year = w["publication_year"]
    short, full, kind = venue_labels(src, doi, year, TYPE_MAP.get(w["type"], "journal"))
    authors = [a["author"]["display_name"] for a in w["authorships"]]
    return entry_yaml(w["title"], authors, short, full, year, w["publication_date"], kind, doi,
                      f"  openalex: {w['id'].rsplit('/', 1)[-1]}")


def scholar_to_yaml(row):
    """(date, YAML entry) for a Scholar-only paper, enriched from Crossref when possible."""
    item = crossref_by_title(row["title"])
    if item:
        parts = ((item.get("issued") or {}).get("date-parts") or [[row["year"]]])[0] + [1, 1]
        year, date = parts[0], f"{parts[0]}-{parts[1]:02d}-{parts[2]:02d}"
        authors = [f"{a.get('given', '')} {a.get('family', '')}".strip() or a.get("name", "") for a in item.get("author", [])]
        # For book chapters the first container is the series ("Lecture Notes in Computer Science"),
        # which venue_labels() resolves to the conference acronym via Crossref.
        src = (item.get("container-title") or [""])[0]
        short, full, kind = venue_labels(src, item["DOI"], year, CROSSREF_TYPES.get(item.get("type"), "journal"))
        return date, entry_yaml(item["title"][0], authors, short, full, year, date, kind, item["DOI"],
                                "  source: scholar", "Found on Google Scholar; details from Crossref.")
    authors = [a.strip() for a in row["authors"].split(",") if a.strip()]
    if authors and authors[-1] in ("...", "…"):
        authors[-1] = "et al."
    year = row["year"] or datetime.date.today().year
    venue = row["venue"].lower()
    kind = ("preprint" if "arxiv" in venue else
            "conference" if re.search(r"workshop|conference|proceedings|symposium|miccai", venue) else "journal")
    short, full, kind = venue_labels(row["venue"], "", year, kind)
    date = f"{year}-01-01"
    return date, entry_yaml(row["title"], authors, short, full, year, date, kind, "", "  source: scholar",
                            "Found on Google Scholar only: complete the author list (Scholar abbreviates and "
                            "truncates it), check the venue, and add a link.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", type=int, default=datetime.date.today().year - 2,
                    help="only look at works published in or after this year (default: two years ago)")
    ap.add_argument("--dry-run", action="store_true", help="print new entries instead of writing them")
    ap.add_argument("--no-scholar", action="store_true", help="skip Google Scholar and use OpenAlex only")
    args = ap.parse_args()

    titles, dois, ids = existing_keys()
    skip = ignored()
    works = fetch_works(args.since)
    scholar = [] if args.no_scholar else [r for r in fetch_scholar() if (r["year"] or 9999) >= args.since]
    on_scholar = {norm(r["title"]) for r in scholar}

    # OpenAlex often holds several records of one paper (preprint, published
    # version, repository copy). Group them by title, accept the group if any
    # record carries a known affiliation or the paper is on your Scholar
    # profile, and keep the best record: published before preprint, then one
    # with a DOI, then the earliest.
    groups = {}
    for w in works:
        if w["type"] not in SKIP_TYPES and norm(w["title"]):
            groups.setdefault(norm(w["title"]), []).append(w)

    def rank(w):
        return (w["type"] == "preprint", not w.get("doi"), w["publication_date"])

    entries = []  # (date, yaml)
    for t, copies in groups.items():
        oids = {c["id"].rsplit("/", 1)[-1] for c in copies}
        cdois = {(c.get("doi") or "").replace("https://doi.org/", "").lower() for c in copies} - {""}
        if t in titles or oids & ids or cdois & dois or ({t} | {o.lower() for o in oids} | cdois) & skip:
            continue
        if t not in on_scholar and not any(key in inst for c in copies for inst in my_institutions(c) for key in AFFILIATIONS):
            print(f"skipped (no matching affiliation): {copies[0]['title'][:80]}", file=sys.stderr)
            continue
        best = min(copies, key=rank)
        entries.append((best["publication_date"], to_yaml(best)))
    from_openalex = len(entries)

    # Papers on Scholar that OpenAlex doesn't have (yet).
    for row in scholar:
        t = norm(row["title"])
        if not t or t in titles or t in groups or t in skip:
            continue
        entries.append(scholar_to_yaml(row))
        titles.add(t)

    entries.sort(key=lambda e: str(e[0]), reverse=True)
    if not entries:
        print("No new publications found.", file=sys.stderr)
        return
    block = "\n\n".join(e[1] for e in entries)
    if args.dry_run:
        print(block)
    else:
        # Insert above the first existing entry so the file stays newest-first.
        stamp = datetime.date.today().isoformat()
        text = PUBS_FILE.read_text() if PUBS_FILE.exists() else ""
        m = re.search(r"^(# .*\n)*- title:", text, re.M)
        at = m.start() if m else len(text)
        note = f"# Added by scripts/sync_publications.py on {stamp}: check authors, venue and topics.\n"
        PUBS_FILE.write_text(text[:at] + note + block + "\n\n" + text[at:])
    summary = f"{len(entries)} new publication(s): {from_openalex} from OpenAlex, {len(entries) - from_openalex} from Google Scholar"
    print(summary + (" (dry run)." if args.dry_run else f", added to {PUBS_FILE.relative_to(ROOT)}."), file=sys.stderr)


if __name__ == "__main__":
    main()

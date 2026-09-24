#!/usr/bin/env python3
"""Find publications on OpenAlex that are not yet in _data/publications.yml.

New works are appended to the YAML file with `selected: false` so they show up
in the full list but not on the homepage. Review the diff before publishing:
OpenAlex occasionally attributes someone else's paper to you, and conference
papers are often listed under "Lecture Notes in Computer Science" instead of
the conference name.

Usage:
    python3 scripts/sync_publications.py            # append new works
    python3 scripts/sync_publications.py --dry-run  # print them instead
    python3 scripts/sync_publications.py --since 2020

Standard library only, so it runs anywhere Python 3.8+ is available.
"""

import argparse
import datetime
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ORCID = "0000-0002-6995-2312"
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


def to_yaml(w):
    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    authors = ", ".join(q(a["author"]["display_name"]) for a in w["authorships"])
    kind = TYPE_MAP.get(w["type"], "journal")
    short, full = SHORT_VENUES.get(src, src), src
    if "arxiv" in src.lower():
        full = "arXiv preprint"
    # "2022 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)" -> "CVPR 2022"
    acr = re.search(r"\(([A-Z][A-Za-z]{2,})\)\s*$", src)
    if src not in SHORT_VENUES and acr:
        short, kind = f"{acr.group(1)} {w['publication_year']}", "conference"
    if doi and (not src or "lecture notes" in src.lower() or "communications in computer" in src.lower()):
        acronym, name = crossref_event(doi)
        if acronym or name:
            label = acronym or name
            year = str(w["publication_year"])
            short = label if label.endswith(year) else f"{label} {year}"
            full, kind = name or full, "conference"
    lines = [f"- title: {q(w['title'])}", f"  authors: [{authors}]"]
    if short:
        lines.append(f"  venue: {q(short)}")
    else:
        lines.append('  venue: ""  # TODO: add venue')
    lines += [f"  venue_full: {q(full)}", f"  year: {w['publication_year']}",
              f"  date: {w['publication_date']}", f"  type: {kind}"]
    if doi:
        lines += [f"  doi: {q(doi)}", "  links:", f"    paper: {q('https://doi.org/' + doi)}"]
    lines += ["  selected: false", "  topics: []", f"  openalex: {w['id'].rsplit('/', 1)[-1]}"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", type=int, default=datetime.date.today().year - 2,
                    help="only look at works published in or after this year (default: two years ago)")
    ap.add_argument("--dry-run", action="store_true", help="print new entries instead of writing them")
    args = ap.parse_args()

    titles, dois, ids = existing_keys()
    skip = ignored()
    works = fetch_works(args.since)

    # OpenAlex often holds several records of one paper (preprint, published
    # version, repository copy). Group them by title, accept the group if any
    # record carries a known affiliation, and keep the best record: published
    # before preprint, then one with a DOI, then the earliest.
    groups = {}
    for w in works:
        if w["type"] not in SKIP_TYPES and norm(w["title"]):
            groups.setdefault(norm(w["title"]), []).append(w)

    def rank(w):
        return (w["type"] == "preprint", not w.get("doi"), w["publication_date"])

    new = []
    for t, copies in groups.items():
        oids = {c["id"].rsplit("/", 1)[-1] for c in copies}
        cdois = {(c.get("doi") or "").replace("https://doi.org/", "").lower() for c in copies} - {""}
        if t in titles or oids & ids or cdois & dois or ({t} | {o.lower() for o in oids} | cdois) & skip:
            continue
        if not any(key in inst for c in copies for inst in my_institutions(c) for key in AFFILIATIONS):
            print(f"skipped (no matching affiliation): {copies[0]['title'][:80]}", file=sys.stderr)
            continue
        new.append(min(copies, key=rank))

    new.sort(key=lambda w: w["publication_date"], reverse=True)
    if not new:
        print("No new publications found.", file=sys.stderr)
        return
    block = "\n\n".join(to_yaml(w) for w in new)
    if args.dry_run:
        print(block)
    else:
        # Insert above the first existing entry so the file stays newest-first.
        stamp = datetime.date.today().isoformat()
        text = PUBS_FILE.read_text() if PUBS_FILE.exists() else ""
        m = re.search(r"^- title:", text, re.M)
        at = m.start() if m else len(text)
        note = f"# Added by scripts/sync_publications.py on {stamp}: check authors, venue and topics.\n"
        PUBS_FILE.write_text(text[:at] + note + block + "\n\n" + text[at:])
    print(f"{len(new)} new publication(s){' (dry run)' if args.dry_run else ' appended to ' + str(PUBS_FILE.relative_to(ROOT))}.",
          file=sys.stderr)


if __name__ == "__main__":
    main()

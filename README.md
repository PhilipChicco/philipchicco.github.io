# philipchicco.github.io

Personal academic site, built with Jekyll and served by GitHub Pages.
Content lives in `_data/` as YAML files, so most updates never touch HTML.

## Common updates

| To… | Edit |
| --- | --- |
| Add a paper | `_data/publications.yml`, or let the weekly sync do it (below) |
| Feature a paper on the homepage | set `selected: true` on it |
| Mark a paper as a highlight (e.g. Nature Portfolio) | add `highlight: "Nature Portfolio"` |
| Announce a paper in News | add `news: "One-line announcement"` to the paper |
| Post other news (talks, awards, roles) | `_data/news.yml` |
| Reviewing, editorial and organizing roles | `_data/service.yml` |
| Positions, education, mentoring | `_data/experience.yml` |
| Research areas | `_data/research.yml` (papers link via their `topics`) |
| Name, role, links, interests | `profile:` in `_config.yml` |
| CV | replace `assets/files/resume.pdf` |
| Colours | the tokens at the top of `assets/css/main.css` |

Each YAML file starts with a comment that explains its fields.

## Publications sync

`scripts/sync_publications.py` asks OpenAlex for works linked to ORCID
0000-0002-6995-2312 and inserts any new ones at the top of
`_data/publications.yml`. It only accepts works where your authorship lists
Harvard, DGIST or Chonbuk, merges duplicate records (preprint vs. published),
and looks up real conference names (e.g. "MICCAI 2024") on Crossref.

```bash
python3 scripts/sync_publications.py --dry-run   # preview
python3 scripts/sync_publications.py             # write
```

A GitHub Action (`.github/workflows/sync-publications.yml`) runs this every
Monday and opens a pull request for you to review. Anything that shouldn't be
added goes in `scripts/publications_ignore.txt`.

## Local preview

```bash
bundle exec jekyll serve --livereload
```

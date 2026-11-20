"""Generate the results lists for the publications pages from docs/shared/results/.

Each entry is a Markdown file with a YAML front matter header and a free Markdown body:

    ---
    type: talk               # publication | talk | workshop | code
    date: 2026-03-12         # sorting and year heading
    lang: de                 # or [de, en] for a bilingual entry
    topics: [hci]            # optional: cs | psy | hci
    title: Beispielvortrag   # bilingual: {de: ..., en: ...} or one shared title
    ---

    Free Markdown body.

A bilingual entry splits its body with `<!-- de -->` and `<!-- en -->` marker lines.
Files and folders starting with "_" (e.g. the templates) are skipped.

Writes docs/shared/generated/results.de.md and results.en.md, which the language pages
include. Run with --watch to regenerate whenever an entry changes.
"""

import argparse
import datetime
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/shared/results"
OUTPUT = ROOT / "docs/shared/generated"
LANGUAGES = ("de", "en")

TYPES = {
    "publication": {"de": "Publikation", "en": "Publication"},
    "talk": {"de": "Vortrag", "en": "Talk"},
    "workshop": {"de": "Workshop", "en": "Workshop"},
    "code": {"de": "PoC / Code", "en": "PoC / Code"},
}
TOPICS = {
    "cs": "Computer Security",
    "psy": "Psychology",
    "hci": "Human-Computer Interaction",
}
FIELDS = {"type", "date", "lang", "topics", "title"}
MARKER = re.compile(r"^<!--\s*(de|en)\s*-->[ \t]*$", re.MULTILINE)


class EntryError(ValueError):
    pass


@dataclass
class Entry:
    path: Path
    type: str
    date: datetime.date
    languages: tuple
    topics: tuple
    titles: dict  # language -> title
    bodies: dict  # language -> body


def display(path):
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def parse_entry(path):
    def fail(message):
        raise EntryError(f"{display(path)}: {message}")

    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.DOTALL)
    if not match:
        fail("missing front matter (the file must start with a '---' header block)")
    try:
        meta = yaml.safe_load(match[1]) or {}
    except yaml.YAMLError as error:
        fail(f"invalid front matter: {error}")
    if not isinstance(meta, dict):
        fail("front matter must contain key: value pairs")
    body = match[2]

    unknown = set(meta) - FIELDS
    if unknown:
        fail(f"unknown field(s) {', '.join(sorted(unknown))}; allowed: {', '.join(sorted(FIELDS))}")
    for field in ("type", "date", "lang", "title"):
        if field not in meta:
            fail(f"missing field '{field}'")

    if meta["type"] not in TYPES:
        fail(f"unknown type {meta['type']!r}; use one of {', '.join(TYPES)}")
    date = meta["date"]
    if isinstance(date, datetime.datetime) or not isinstance(date, datetime.date):
        fail(f"date must be written as YYYY-MM-DD, not {date!r}")

    languages = meta["lang"] if isinstance(meta["lang"], list) else [meta["lang"]]
    if not languages or len(set(languages)) != len(languages) or not set(languages) <= set(LANGUAGES):
        fail(f"lang must be 'de', 'en' or [de, en], not {meta['lang']!r}")

    topics = meta.get("topics") or []
    if not isinstance(topics, list) or not set(topics) <= set(TOPICS):
        fail(f"topics must be a list of {', '.join(TOPICS)}, not {meta.get('topics')!r}")

    title = meta["title"]
    if isinstance(title, dict):
        if set(title) != set(languages):
            fail(f"title needs exactly one entry per language ({', '.join(languages)})")
        titles = title
    else:
        titles = {language: title for language in languages}
    for value in titles.values():
        if not isinstance(value, str) or not value.strip() or "\n" in value.strip():
            fail("title must be a single line of text")
    titles = {language: value.strip() for language, value in titles.items()}

    markers = MARKER.findall(body)
    if len(languages) == 1:
        if markers:
            fail("language markers are only allowed in bilingual entries (lang: [de, en])")
        bodies = {languages[0]: body.strip()}
    else:
        if sorted(markers) != sorted(languages):
            fail("a bilingual entry needs one '<!-- de -->' and one '<!-- en -->' line in its body")
        parts = MARKER.split(body)
        if parts[0].strip():
            fail("text before the first language marker; put it under '<!-- de -->' or '<!-- en -->'")
        bodies = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}

    return Entry(path, meta["type"], date, tuple(languages), tuple(topics), titles, bodies)


def load_entries(source=SOURCE, include_hidden=False):
    paths = sorted(
        path for path in source.rglob("*.md")
        if include_hidden or not any(part.startswith("_") for part in path.relative_to(source).parts)
    )
    entries = [parse_entry(path) for path in paths]
    # Newest first; the file name keeps the order stable for entries on the same day.
    return sorted(entries, key=lambda entry: (entry.date, entry.path.name), reverse=True)


def render_entry(entry, language):
    # A bilingual entry is shown in the page language, any other in its own language.
    content_language = language if language in entry.languages else entry.languages[0]
    lines = [
        f'<div class="daisy-result" data-type="{entry.type}" lang="{content_language}" markdown="1">',
        "",
        f'<p class="daisy-result-type" lang="{language}">{TYPES[entry.type][language]}</p>',
        "",
        f"### {entry.titles[content_language]}",
        "",
    ]
    if entry.topics:
        lines += [
            *(f'<span class="daisy-publication-tag {topic}" lang="en">{TOPICS[topic]}</span>'
              for topic in entry.topics),
            "",
        ]
    if entry.bodies[content_language]:
        lines += [entry.bodies[content_language], ""]
    lines += ["</div>", ""]
    return lines


def render(entries, language):
    lines = [
        "<!-- Generated by scripts/build_results.py from docs/shared/results/. Do not edit. -->",
        "",
        '<div class="daisy-publications" markdown="1">',
        "",
    ]
    year = None
    for entry in entries:
        if entry.date.year != year:
            year = entry.date.year
            lines += [f"## {year}", ""]
        lines += render_entry(entry, language)
    lines += ["</div>", ""]
    return "\n".join(lines)


def build(source=SOURCE, output=OUTPUT):
    entries = load_entries(source)
    output.mkdir(parents=True, exist_ok=True)
    # Keep the generated files out of git without needing an entry in the root .gitignore.
    ignore = output / ".gitignore"
    if not ignore.exists():
        ignore.write_text("# Generated by scripts/build_results.py\n*\n", encoding="utf-8")
    for language in LANGUAGES:
        target = output / f"results.{language}.md"
        content = render(entries, language)
        # Only write on change, so the preview server does not reload needlessly.
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            target.write_text(content, encoding="utf-8")
    return entries


def watch(source=SOURCE, output=OUTPUT):
    def snapshot():
        return {path: path.stat().st_mtime_ns for path in source.rglob("*.md")}

    print(f"Watching {display(source)} (Ctrl+C to stop)", flush=True)
    last = None
    while True:
        current = snapshot()
        if current != last:
            last = current
            try:
                entries = build(source, output)
                print(f"{time.strftime('%H:%M:%S')} Generated {len(entries)} result(s)", flush=True)
            except EntryError as error:
                print(f"{time.strftime('%H:%M:%S')} Error: {error}", file=sys.stderr, flush=True)
        time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--watch", action="store_true", help="regenerate whenever an entry changes")
    args = parser.parse_args()
    if args.watch:
        try:
            watch()
        except KeyboardInterrupt:
            pass
        return
    try:
        entries = build()
    except EntryError as error:
        sys.exit(f"Error: {error}")
    print(f"Generated {len(entries)} result(s) in {display(OUTPUT)}")


if __name__ == "__main__":
    main()

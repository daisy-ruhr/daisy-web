import html
import json
import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", namespace)

german_sitemap_path = Path("site/de/sitemap.xml")
english_sitemap_path = Path("site/en/sitemap.xml")
sitemap_path = Path("site/sitemap.xml")
sitemap = ET.parse(german_sitemap_path)
english_sitemap = ET.parse(english_sitemap_path)

for entry in english_sitemap.getroot().findall(f"{{{namespace}}}url"):
    sitemap.getroot().append(entry)

sitemap.write(sitemap_path, encoding="utf-8", xml_declaration=True)

shutil.copyfile("overrides/language-landing.html", "site/index.html")
for source in Path("docs/de").rglob("*.md"):
    relative = source.relative_to("docs/de")
    page = relative.parent if relative.name == "index.md" else relative.with_suffix("")
    if page == Path("."):
        continue
    if page.parts[0] in ("de", "en", "assets"):
        raise ValueError(f"Legacy page conflicts with a reserved output path: {relative}")
    directory = Path("site") / page
    directory.mkdir(parents=True, exist_ok=True)
    target = quote(os.path.relpath(Path("site/de") / page, directory).replace(os.sep, "/") + "/", safe="/")
    escaped = html.escape(target, quote=True)
    (directory / "index.html").write_text(
        '<!doctype html>\n<html lang="de"><head><meta charset="utf-8">\n'
        f'<meta http-equiv="refresh" content="0; url={escaped}">\n'
        f'<script>location.replace({json.dumps(target)} + location.search + location.hash);</script>\n'
        f'</head><body><a href="{escaped}">Weiter zur deutschen Seite</a></body></html>\n',
        encoding="utf-8",
    )

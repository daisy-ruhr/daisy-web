import functools
import http.server
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import tomllib
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urljoin, urlsplit

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


def post_metadata(source, language):
    if source.relative_to(ROOT / "docs" / language).parts[:2] == ("news", "posts"):
        return yaml.safe_load(source.read_text(encoding="utf-8").split("---", 2)[1])
    return None


def published_source(source, language):
    metadata = post_metadata(source, language)
    return not metadata or not metadata.get("draft", False)


def output_page(source, language):
    relative = source.relative_to(ROOT / "docs" / language)
    metadata = post_metadata(source, language)
    if metadata is not None:
        return Path("news") / metadata["slug"]
    return relative.parent if relative.name == "index.md" else relative.with_suffix("")


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_header = False
        self.language_links = {}
        self.language_targets = {}
        self.alternates = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "header":
            self.in_header = True
        elif tag == "a" and self.in_header and "md-select__link" in attrs.get("class", "").split():
            self.language_links[attrs["hreflang"]] = attrs["href"]
            self.language_targets[attrs["hreflang"]] = attrs.get("target")
        elif tag == "link" and attrs.get("rel") == "alternate" and "hreflang" in attrs:
            self.alternates[attrs["hreflang"]] = attrs["href"]

    def handle_endtag(self, tag):
        if tag == "header":
            self.in_header = False


class RenderedPage(HTMLParser):
    def __init__(self):
        super().__init__()
        self.html = {}
        self.body = {}
        self.meta = {}
        self.resources = []
        self.title = ""
        self.in_title = False
        self.ellipsis_depth = 0
        self.ellipsis_text = ""
        self.labels = set()
        self.palette_labels = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.html = attrs
        elif tag == "body":
            self.body = attrs
        elif tag == "meta" and "name" in attrs:
            self.meta[attrs["name"]] = attrs.get("content")
        elif tag == "title":
            self.in_title = True
        elif tag == "link" and attrs.get("rel") in ("stylesheet", "icon"):
            self.resources.append(attrs["href"])
        elif tag == "img" and "src" in attrs:
            self.resources.append(attrs["src"])
        elif tag == "input" and attrs.get("name") == "__palette":
            self.palette_labels[attrs["data-md-color-scheme"]] = attrs["aria-label"]
        if self.ellipsis_depth:
            self.ellipsis_depth += 1
        elif tag == "span" and "md-ellipsis" in attrs.get("class", "").split():
            self.ellipsis_depth = 1
            self.ellipsis_text = ""

    def handle_data(self, data):
        if self.in_title:
            self.title += data
        if self.ellipsis_depth:
            self.ellipsis_text += data

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if self.ellipsis_depth:
            self.ellipsis_depth -= 1
            if not self.ellipsis_depth:
                self.labels.add(self.ellipsis_text.strip())


class SiteTests(unittest.TestCase):
    def test_language_configs_share_theme_settings(self):
        with (ROOT / "zensical.toml").open("rb") as file:
            german = tomllib.load(file)["project"]
        with (ROOT / "zensical.en.toml").open("rb") as file:
            english = tomllib.load(file)["project"]
        for key in ("site_author", "extra_css", "extra_javascript", "watch", "markdown_extensions", "plugins"):
            self.assertEqual(english[key], german[key], key)
        for key in ("variant", "font", "favicon", "custom_dir", "features"):
            self.assertEqual(english["theme"][key], german["theme"][key], key)
        for original, localized in zip(german["theme"]["palette"], english["theme"]["palette"], strict=True):
            self.assertEqual(original["scheme"], localized["scheme"])
            self.assertEqual(original["primary"], localized["primary"])
            self.assertEqual(original["accent"], localized["accent"])
            self.assertEqual(original["toggle"]["icon"], localized["toggle"]["icon"])
        self.assertEqual(english["site_url"], "https://daisy.ruhr/en/")

    def test_localized_navigation_and_palette(self):
        for prefix, labels, palette in (
            ("de/", {"Projekt", "News", "Ergebnisse", "Team"},
             {"slate": "Zu hellem Modus wechseln", "default": "Zu dunklem Modus wechseln"}),
            ("en/", {"Project", "News", "Results", "Team"},
             {"slate": "Switch to light mode", "default": "Switch to dark mode"}),
        ):
            with self.subTest(language=prefix or "de"):
                parser = RenderedPage()
                parser.feed((SITE / prefix / "index.html").read_text(encoding="utf-8"))
                self.assertLessEqual(labels, parser.labels)
                self.assertEqual(parser.palette_labels, palette)

    def test_theme_configuration_and_assets(self):
        for language, prefix, site_name, description in (
            ("de", "de/", "DAISY", "Datenschutz und Arbeitnehmendeninteressen in AI-as-a-Service-Systemen"),
            ("en", "en/", "DAISY", "Data Protection and Employee Interests in AI-as-a-Service Systems"),
        ):
            with self.subTest(language=language):
                assets = ROOT / "overrides" / "assets"
                self.assertTrue(assets.is_dir())
                self.assertFalse(assets.is_symlink())
                for source in assets.rglob("*"):
                    if source.is_file():
                        output = SITE / prefix / "assets" / source.relative_to(assets)
                        self.assertTrue(output.is_file(), f"Missing generated asset: {output}")
                        self.assertEqual(source.read_bytes(), output.read_bytes())
                own_image = f"bmftr_{language}.png"
                self.assertTrue((SITE / prefix / "assets/img" / own_image).is_file())

                for source in sorted((ROOT / "docs" / language).rglob("*.md")):
                    if not published_source(source, language):
                        continue
                    page_path = output_page(source, language)
                    page_url = "" if str(page_path) == "." else f"{page_path.as_posix()}/"
                    file = SITE / prefix / page_path / "index.html"
                    parser = RenderedPage()
                    parser.feed(file.read_text(encoding="utf-8"))
                    self.assertEqual(parser.html.get("lang"), language)
                    # Check that the page title ends with the site name
                    self.assertRegex(parser.title, rf".+ - {re.escape(site_name)}$")
                    self.assertEqual(parser.meta.get("description"), description)
                    self.assertEqual(parser.body.get("data-md-color-scheme"), "slate")
                    self.assertEqual(parser.body.get("data-md-color-primary"), "custom")
                    self.assertEqual(parser.body.get("data-md-color-accent"), "custom")
                    self.assertTrue(any(url.endswith("assets/styles/extra.css") for url in parser.resources))
                    self.assertTrue(any(url.endswith("assets/img/favicon.svg") for url in parser.resources))
                    for resource in parser.resources:
                        url = urlsplit(urljoin(f"https://example.org/{prefix}{page_url}", resource))
                        if url.netloc == "example.org":
                            self.assertTrue((SITE / url.path.lstrip("/")).is_file(), f"{file}: missing {resource}")
                        else:
                            self.fail(f"{file}: unexpected external resource {resource}")

    def test_language_links_and_alternates(self):
        german_pages = {path.relative_to(ROOT / "docs/de") for path in (ROOT / "docs/de").rglob("*.md")}
        english_pages = {path.relative_to(ROOT / "docs/en") for path in (ROOT / "docs/en").rglob("*.md")}
        self.assertEqual(german_pages, english_pages)
        self.assertTrue(german_pages)

        for source in sorted(german_pages):
            german_source = ROOT / "docs/de" / source
            english_source = ROOT / "docs/en" / source
            german_post = post_metadata(german_source, "de")
            english_post = post_metadata(english_source, "en")
            if german_post is not None:
                for key in ("slug", "date", "draft"):
                    self.assertEqual(german_post.get(key), english_post.get(key), (source, key))
            if not published_source(german_source, "de"):
                continue
            page_path = output_page(german_source, "de")
            self.assertEqual(page_path, output_page(english_source, "en"))
            page_url = "" if str(page_path) == "." else f"{page_path.as_posix()}/"
            for language in ("de", "en"):
                prefix = f"{language}/"
                file = SITE / prefix / page_path / "index.html"
                with self.subTest(page=str(source), language=language):
                    parser = PageLinks()
                    parser.feed(file.read_text(encoding="utf-8"))
                    self.assertEqual(set(parser.language_links), {"de", "en"})
                    self.assertEqual(set(parser.language_targets.values()), {"_self"})
                    self.assertEqual(set(parser.alternates), {"de", "en"})
                    for target, target_prefix in (("de", "de/"), ("en", "en/")):
                        # Exercise the relative links both at the domain root and under a URL prefix.
                        for base in ("https://example.org/", "https://example.org/preview/"):
                            current = urljoin(base, prefix + page_url)
                            expected = urljoin(base, target_prefix + page_url)
                            self.assertEqual(urljoin(current, parser.language_links[target]), expected)
                        self.assertEqual(
                            urlsplit(parser.alternates[target]).path,
                            "/" + target_prefix + page_url,
                        )
                        self.assertTrue((SITE / target_prefix / page_path / "index.html").is_file())

    def test_sitemap_and_legacy_redirects(self):
        class RedirectPage(HTMLParser):
            def __init__(self):
                super().__init__()
                self.target = None

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "meta" and attrs.get("http-equiv", "").lower() == "refresh":
                    self.target = attrs["content"].split("url=", 1)[1]

        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        sitemap = ET.parse(SITE / "sitemap.xml")
        urls = {entry.text for entry in sitemap.findall("s:url/s:loc", namespace)}
        for language in ("de", "en"):
            for source in (ROOT / "docs" / language).rglob("*.md"):
                if not published_source(source, language):
                    continue
                relative = source.relative_to(ROOT / "docs" / language)
                page = output_page(source, language)
                suffix = "" if page == Path(".") else f"{page.as_posix()}/"
                self.assertIn(f"https://daisy.ruhr/{language}/{suffix}", urls)
                if language == "de" and suffix and relative.parts[0] != "news":
                    old_page = SITE / page / "index.html"
                    content = old_page.read_text(encoding="utf-8")
                    parser = RedirectPage()
                    parser.feed(content)
                    self.assertIsNotNone(parser.target)
                    for base in ("https://example.org/", "https://example.org/preview/"):
                        self.assertEqual(
                            urljoin(urljoin(base, suffix), parser.target),
                            urljoin(base, f"de/{suffix}"),
                        )
                    self.assertIn("location.search + location.hash", content)

    def test_language_search_indexes(self):
        for language in ("de", "en"):
            with self.subTest(language=language):
                search = json.loads((SITE / language / "search.json").read_text(encoding="utf-8"))
                self.assertIn(language, search["config"]["lang"])
                self.assertIn("publications/", [item["location"] for item in search["items"]])

    def test_news_pages(self):
        for language, title in (("de", "KI in Unternehmen sicher nutzen"),
                                ("en", "Using AI safely in companies")):
            with self.subTest(language=language):
                overview = (SITE / language / "news/index.html").read_text(encoding="utf-8")
                post = (SITE / language / "news/using-ai-safely/index.html").read_text(encoding="utf-8")
                home = (SITE / language / "index.html").read_text(encoding="utf-8")
                self.assertIn('class="md-post md-post--excerpt"', overview)
                self.assertIn('datetime="2026-09-29', overview)
                self.assertIn(title, overview)
                self.assertIn(title, post)
                self.assertIn("assets/img/daisy_staff.webp", post)
                self.assertIn('class="daisy-latest-news"', home)
                self.assertIn("assets/javascripts/news.js", home)
                search = json.loads((SITE / language / "search.json").read_text(encoding="utf-8"))
                self.assertTrue(any(item["location"].startswith("news/using-ai-safely/")
                                    for item in search["items"]))

    def test_news_chronology_and_drafts(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            shutil.copytree(ROOT / "docs", project / "docs")
            shutil.copytree(ROOT / "overrides", project / "overrides")
            shutil.copyfile(ROOT / "zensical.toml", project / "zensical.toml")
            posts = project / "docs/de/news/posts"
            for day in range(2, 7):
                draft = "draft: true\n" if day == 6 else ""
                (posts / f"test-{day}.md").write_text(
                    f"---\ndate: 2026-09-{day:02d}\nslug: test-{day}\n{draft}---\n\n"
                    f"# Test {day}\n\nIntroduction.\n\n<!-- more -->\n\nDetails.\n",
                    encoding="utf-8",
                )
            subprocess.run([sys.executable, "-m", "zensical", "build", "--strict"],
                           cwd=project, check=True, capture_output=True, text=True)
            overview = (project / "site/de/news/index.html").read_text(encoding="utf-8")
            dates = re.findall(r'<time datetime="(2026-09-\d\d)', overview)
            self.assertEqual(dates, ["2026-09-29"] + [f"2026-09-{day:02d}" for day in range(5, 1, -1)])
            self.assertNotIn("Test 6", overview)
            self.assertFalse((project / "site/de/news/test-6/index.html").exists())

    def test_shared_publications(self):
        class PublicationsParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.links = []
                self.tags = []
                self.text = ""

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                if tag == "a":
                    self.links.append(attrs)
                if "daisy-publication-tag" in attrs.get("class", "").split():
                    self.tags.append(attrs)

            def handle_data(self, data):
                self.text += data

        shared = (ROOT / "docs/shared/publications.md").read_text(encoding="utf-8")
        for language in ("de", "en"):
            with self.subTest(language=language):
                built = (SITE / language / "publications/index.html").read_text(encoding="utf-8")
                parser = PublicationsParser()
                parser.feed(built)
                self.assertIn('class="daisy-publications"', built)
                self.assertNotIn("Example journal article", parser.text)
                self.assertNotIn("example-journal", json.dumps(json.loads(
                    (SITE / language / "search.json").read_text(encoding="utf-8"))))

        # Render the same uncommented examples through the configured snippet mechanism.
        with tempfile.TemporaryDirectory() as directory:
            snippet = Path(directory) / "publications.md"
            example = shared.split("<!--\n", 1)[1].split("\n-->", 1)[0]
            snippet.write_text(f'<div class="daisy-publications" markdown="1">\n\n{example}\n\n</div>',
                               encoding="utf-8")
            for language in ("de", "en"):
                with self.subTest(language=language, examples="enabled"):
                    page = (ROOT / "docs" / language / "publications.md").read_text(encoding="utf-8")
                    page = page.replace("docs/shared/publications.md", snippet.name)
                    rendered = markdown.markdown(
                        page,
                        extensions=["pymdownx.snippets", "md_in_html", "attr_list"],
                        extension_configs={"pymdownx.snippets": {
                            "base_path": [directory], "check_paths": True,
                        }},
                    )
                    parser = PublicationsParser()
                    parser.feed(rendered)
                    self.assertIn("Example journal article", parser.text)
                    self.assertIn("Example conference paper", parser.text)
                    self.assertEqual(len(parser.tags), 3)
                    for category in ("tech", "psy", "inter"):
                        self.assertTrue(any(category in tag["class"].split() for tag in parser.tags))
                    for doi in ("10.XXXX/example-journal", "10.XXXX/example-conference"):
                        self.assertTrue(any(
                            link.get("href") == f"https://doi.org/{doi}"
                            and "md-button" in link.get("class", "").split()
                            for link in parser.links
                        ))

    def test_publication_category_colors(self):
        css = (ROOT / "overrides/assets/styles/extra.css").read_text(encoding="utf-8")
        for category in ("tech", "psy", "inter"):
            for prefix in ("", "[data-md-color-scheme=slate] "):
                selector = f"{prefix}.md-typeset .daisy-publication-tag.{category}"
                with self.subTest(selector=selector):
                    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
                    self.assertIsNotNone(match)
                    color = re.search(r"(?<![\w-])color:\s*(#[0-9a-fA-F]{6})\s*;", match[1])
                    border = re.search(r"border-color:\s*(#[0-9a-fA-F]{6})\s*;", match[1])
                    self.assertIsNotNone(color)
                    self.assertIsNotNone(border)
                    self.assertEqual(color[1].lower(), border[1].lower())

    def test_language_links_over_http(self):
        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

        handler = functools.partial(QuietHandler, directory=str(SITE))
        with http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}/"
                for source in sorted((ROOT / "docs/de").rglob("*.md")):
                    if not published_source(source, "de"):
                        continue
                    page_path = output_page(source, "de")
                    page_url = "" if str(page_path) == "." else f"{page_path.as_posix()}/"
                    for prefix in ("de/", "en/"):
                        current = urljoin(base, prefix + page_url)
                        with self.subTest(page=str(source), language=prefix or "de"):
                            with urlopen(current) as response:
                                parser = PageLinks()
                                parser.feed(response.read().decode("utf-8"))
                            for language, link in parser.language_links.items():
                                with urlopen(urljoin(current, link)) as response:
                                    target = RenderedPage()
                                    target.feed(response.read().decode("utf-8"))
                                    self.assertEqual(response.status, 200)
                                    self.assertEqual(target.html.get("lang"), language)
            finally:
                server.shutdown()
                thread.join()


if __name__ == "__main__":
    unittest.main()

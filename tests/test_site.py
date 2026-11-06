import functools
import http.server
import threading
import tomllib
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urljoin, urlsplit

from scripts.site import english_config


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_header = False
        self.language_links = {}
        self.alternates = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "header":
            self.in_header = True
        elif tag == "a" and self.in_header and "md-select__link" in attrs.get("class", "").split():
            self.language_links[attrs["hreflang"]] = attrs["href"]
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
    def test_english_config_inherits_shared_settings(self):
        with (ROOT / "zensical.toml").open("rb") as file:
            german = tomllib.load(file)["project"]
        english = english_config()
        for key in ("site_author", "extra_css", "watch", "markdown_extensions", "plugins"):
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
            ("", {"Start", "Das Projekt", "Wissenschaftlicher Ansatz", "Arbeitspakete",
                  "Ergebnisse & Transfer", "Rechtlicher Rahmen", "Konsortium & Netzwerk",
                  "Kontakt", "Glossar", "Über DAISY", "Impressum", "Datenschutz"},
             {"slate": "Zu hellem Modus wechseln", "default": "Zu dunklem Modus wechseln"}),
            ("en/", {"Home", "The Project", "Scientific Approach", "Work Packages",
                     "Results & Transfer", "Legal Framework", "Consortium & Network",
                     "Contact", "Glossary", "About DAISY", "Legal Notice", "Privacy Policy"},
             {"slate": "Switch to light mode", "default": "Switch to dark mode"}),
        ):
            with self.subTest(language=prefix or "de"):
                parser = RenderedPage()
                parser.feed((SITE / prefix / "index.html").read_text(encoding="utf-8"))
                self.assertTrue(labels.issubset(parser.labels), labels - parser.labels)
                self.assertEqual(parser.palette_labels, palette)

    def test_theme_configuration_and_assets(self):
        for language, prefix, site_name, description in (
            ("de", "", "Projekt DAISY", "Datenschutz und Arbeitnehmendeninteressen in AI-as-a-Service-Systemen"),
            ("en", "en/", "DAISY Project", "Data Protection and Employee Interests in AI-as-a-Service Systems"),
        ):
            with self.subTest(language=language):
                for source in (ROOT / "assets").rglob("*"):
                    if source.is_file():
                        output = SITE / prefix / "assets" / source.relative_to(ROOT / "assets")
                        self.assertTrue(output.is_file(), f"Missing generated asset: {output}")
                        self.assertEqual(source.read_bytes(), output.read_bytes())

                for source in sorted((ROOT / "docs" / language).rglob("*.md")):
                    relative = source.relative_to(ROOT / "docs" / language)
                    page_path = relative.parent if relative.name == "index.md" else relative.with_suffix("")
                    page_url = "" if str(page_path) == "." else f"{page_path.as_posix()}/"
                    file = SITE / prefix / page_path / "index.html"
                    parser = RenderedPage()
                    parser.feed(file.read_text(encoding="utf-8"))
                    self.assertEqual(parser.html.get("lang"), language)
                    self.assertTrue(parser.title.endswith(site_name))
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
            page_path = source.parent if source.name == "index.md" else source.with_suffix("")
            page_url = "" if str(page_path) == "." else f"{page_path.as_posix()}/"
            for language in ("de", "en"):
                prefix = "en/" if language == "en" else ""
                file = SITE / prefix / page_path / "index.html"
                with self.subTest(page=str(source), language=language):
                    parser = PageLinks()
                    parser.feed(file.read_text(encoding="utf-8"))
                    self.assertEqual(set(parser.language_links), {"de", "en"})
                    self.assertEqual(set(parser.alternates), {"de", "en"})
                    for target, target_prefix in (("de", ""), ("en", "en/")):
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
                    relative = source.relative_to(ROOT / "docs/de")
                    page_path = relative.parent if relative.name == "index.md" else relative.with_suffix("")
                    page_url = "" if str(page_path) == "." else f"{page_path.as_posix()}/"
                    for prefix in ("", "en/"):
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

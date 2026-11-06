import xml.etree.ElementTree as ET
from pathlib import Path

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

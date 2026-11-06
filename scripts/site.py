import argparse
import functools
import http.server
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import urljoin

import yaml


ROOT = Path(__file__).resolve().parents[1]


def english_config():
    with (ROOT / "zensical.toml").open("rb") as file:
        project = tomllib.load(file)["project"]

    localization = project["extra"]["localization"]["en"]
    for key in ("site_name", "site_description", "docs_dir", "site_dir", "nav"):
        project[key] = localization[key]
    alternate = next(item for item in project["extra"]["alternate"] if item["lang"] == "en")
    project["site_url"] = urljoin(project["site_url"].rstrip("/") + "/", alternate["link"].lstrip("/"))
    project["theme"]["language"] = "en"
    for palette in project["theme"]["palette"]:
        palette["toggle"]["name"] = localization["palette_toggle_names"][palette["scheme"]]
    return project


def build():
    subprocess.run(
        [sys.executable, "-m", "zensical", "build", "--config-file", "zensical.toml", "--strict"],
        cwd=ROOT,
        check=True,
    )
    config = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".yml", dir=ROOT, delete=False
    )
    try:
        with config:
            yaml.safe_dump(english_config(), config, allow_unicode=True, sort_keys=False)
        subprocess.run(
            [sys.executable, "-m", "zensical", "build", "--config-file", config.name, "--strict"],
            cwd=ROOT,
            check=True,
        )
    finally:
        Path(config.name).unlink()
    subprocess.run([sys.executable, "scripts/merge_sitemaps.py"], cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description="Build or preview both site languages.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="Build both languages into site/")
    serve_parser = subparsers.add_parser("serve", help="Build and serve both languages")
    serve_parser.add_argument("--bind", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    build()
    if args.command == "serve":
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT / "site"))
        with http.server.ThreadingHTTPServer((args.bind, args.port), handler) as server:
            print(f"Serving both languages at http://{args.bind}:{server.server_port}/", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()

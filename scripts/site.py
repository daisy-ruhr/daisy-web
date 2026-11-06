import argparse
import functools
import http.server
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build():
    for config in ("zensical.toml", "zensical.en.toml"):
        subprocess.run(
            [sys.executable, "-m", "zensical", "build", "--config-file", config, "--strict"],
            cwd=ROOT,
            check=True,
        )
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

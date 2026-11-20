"""Build the complete site into site/: results lists, both languages, sitemap and redirects.

Usage: python scripts/build.py (from any directory, with the project's Python environment)
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    ("Generate results lists", [sys.executable, "scripts/build_results.py"]),
    ("Build German site", [sys.executable, "-m", "zensical", "build", "--strict"]),
    ("Build English site",
     [sys.executable, "-m", "zensical", "build", "--config-file", "zensical.en.toml", "--strict"]),
    ("Merge sitemaps and write redirects", [sys.executable, "scripts/merge_sitemaps.py"]),
]


def main():
    for name, command in STEPS:
        print(f"==> {name}", flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            sys.exit(f"Build failed at step: {name}")
    print("==> Done: site/ is ready")


if __name__ == "__main__":
    main()

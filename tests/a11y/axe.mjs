// Automated accessibility check of the built site with axe-core.
//
// Serves site/ locally, opens every page from site/sitemap.xml (plus the root language
// selection) in light and dark mode at desktop and phone width, and runs axe on it.
// WCAG 2.0/2.1/2.2 A and AA violations fail the check; axe best-practice findings are
// reported as warnings only.
//
// Usage (after building the site, see README):
//   npm ci --prefix tests/a11y
//   node tests/a11y/axe.mjs
// Set CHROME_PATH if Chrome/Chromium is not found automatically.

import { existsSync, readFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const require = createRequire(import.meta.url);
const axeSource = readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");
const SITE = resolve(fileURLToPath(new URL("../../site", import.meta.url)));

const ERROR_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];
const SCHEMES = ["default", "slate"]; // Zensical light and dark palette
const WIDTHS = [1280, 320];          // desktop and WCAG 1.4.10 reflow width

const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png",
  ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp", ".xml": "application/xml",
};

function findChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium",
    "/usr/bin/chromium-browser", "/snap/bin/chromium",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ];
  const found = candidates.find((path) => path && existsSync(path));
  if (!found) throw new Error("No Chrome/Chromium found; set CHROME_PATH.");
  return found;
}

function serve() {
  const server = createServer(async (request, response) => {
    let path = normalize(decodeURIComponent(new URL(request.url, "http://x").pathname));
    if (path.endsWith("/")) path += "index.html";
    const file = join(SITE, path);
    try {
      if (!file.startsWith(SITE)) throw new Error("outside site/");
      const body = await readFile(file);
      response.writeHead(200, { "Content-Type": TYPES[extname(file).toLowerCase()] ?? "application/octet-stream" });
      response.end(body);
    } catch {
      response.writeHead(404).end("Not found");
    }
  });
  return new Promise((done) => server.listen(0, "127.0.0.1", () => done(server)));
}

function pagesFromSitemap() {
  const sitemap = readFileSync(join(SITE, "sitemap.xml"), "utf8");
  const paths = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => new URL(match[1]).pathname);
  return ["/", ...new Set(paths)];
}

const annotate = process.env.GITHUB_ACTIONS === "true";
const server = await serve();
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await puppeteer.launch({ executablePath: findChrome(), headless: true, args: ["--no-sandbox"] });

const findings = new Map(); // rule + element -> details, so repeated layouts are reported once
try {
  for (const path of pagesFromSitemap()) {
    for (const width of WIDTHS) {
      for (const scheme of SCHEMES) {
        const page = await browser.newPage();
        await page.setViewport({ width, height: 900 });
        let response = await page.goto(base + path, { waitUntil: "networkidle0" });
        if (new URL(page.url()).pathname !== path) {
          // The root language selection redirects via JavaScript. Load it without scripts so
          // the page itself is tested, then re-enable JavaScript for axe.
          await page.setJavaScriptEnabled(false);
          response = await page.goto(base + path, { waitUntil: "load" });
          await page.setJavaScriptEnabled(true);
        }
        if (!response?.ok()) throw new Error(`${path}: HTTP ${response?.status()}`);
        // Disable transitions so colours are measured in their final state.
        await page.addStyleTag({ content: "*, *::before, *::after { transition: none !important; animation: none !important; }" });
        await page.evaluate((value) => document.body?.setAttribute("data-md-color-scheme", value), scheme);
        await page.evaluate(axeSource);
        const result = await page.evaluate(
          (tags) => axe.run(document, { runOnly: { type: "tag", values: [...tags, "best-practice"] } }),
          ERROR_TAGS,
        );
        for (const violation of result.violations) {
          const error = violation.tags.some((tag) => ERROR_TAGS.includes(tag));
          for (const node of violation.nodes) {
            const key = `${violation.id} ${node.target.join(" ")}`;
            const finding = findings.get(key) ?? {
              error, rule: violation.id, help: violation.help, url: violation.helpUrl,
              target: node.target.join(" "), summary: node.failureSummary.replace(/\s+/g, " ").trim(),
              where: new Set(),
            };
            finding.where.add(`${path} (${scheme === "slate" ? "dark" : "light"}, ${width}px)`);
            findings.set(key, finding);
          }
        }
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
  server.close();
}

const all = [...findings.values()].sort((a, b) => Number(b.error) - Number(a.error));
for (const finding of all) {
  const where = [...finding.where];
  const label = finding.error ? "ERROR" : "warning";
  console.log(`${label}: [${finding.rule}] ${finding.help}\n  element: ${finding.target}\n  ${finding.summary}\n  on: ${where.slice(0, 3).join("; ")}${where.length > 3 ? ` and ${where.length - 3} more` : ""}\n  ${finding.url}\n`);
  if (annotate) {
    const level = finding.error ? "error" : "warning";
    console.log(`::${level} title=axe ${finding.rule}::${finding.help} – ${finding.target} on ${where[0]}`);
  }
}
const errors = all.filter((finding) => finding.error).length;
console.log(`axe: ${errors} WCAG violation(s), ${all.length - errors} best-practice warning(s).`);
process.exit(errors ? 1 : 0);

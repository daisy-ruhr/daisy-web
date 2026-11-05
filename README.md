# DAISY – Project Website

Static documentation site for the DAISY consortium
(*Datenschutz und Arbeitnehmendeninteressen in AI-as-a-Service-Systemen* – Data Protection
and Employee Interests in AI-as-a-Service Systems).
Built with [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/),
bilingual (German and English), without external JavaScript or CSS libraries – all assets
live in the repository, and no Google Fonts or CDN resources are loaded.

## Development

The Python environment lives in `.venv/` (not checked in).

```bash
python3 -m venv .venv            # once, if the environment is missing
.venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve           # live preview at http://127.0.0.1:8000
```

Note: `source .venv/bin/activate` only affects the shell it is run in. In scripts and CI,
call `.venv/bin/mkdocs` directly instead.

## Build

```bash
.venv/bin/mkdocs build --strict   # fails on broken links and warnings
```

The static output ends up in `site/` (see `.gitignore`).

## Languages

Internationalization is handled by the
[mkdocs-static-i18n](https://ultrabug.github.io/mkdocs-static-i18n/) plugin using a
folder structure:

- `docs/de/` – German (default language, served at the site root `/`)
- `docs/en/` – English (served at `/en/`)

Both folders must use the same file names so the language switcher can map each page to its
translation. Links between pages are relative (e.g. `project.md`), so they stay within the
current language. Shared assets live in `docs/assets/`. Navigation titles are written in
German in `nav` and translated via `nav_translations` in the plugin configuration.

## Maintaining pages

| Task | Location |
| --- | --- |
| Navigation and theme options | `mkdocs.yml` |
| Content | `docs/de/*.md` (German), `docs/en/*.md` (English) – same file names in both folders |
| Colors, hero banner, special blocks | `docs/assets/styles/extra.css` |
| Images and favicon | `docs/assets/img/` |

When editing `mkdocs.yml` or `extra.css`, reload the preview; `mkdocs serve` picks up
changes automatically.

Markdown extensions in use: admonitions (`!!!`), collapsible blocks (`???`),
tabs (`=== "Tab"`), grid cards (`<div class="grid cards" markdown="1">`),
definition lists (`def_list`), `attr_list` and `md_in_html`.

## To clarify before publishing

The site deliberately contains placeholders that must be replaced before going live:

- `site_url` and `repo_url` in `mkdocs.yml` (domain and repository URL)
- Contact e-mail in `mkdocs.yml` and `docs/*/contact.md` (currently `steffen.becker@rub.de`)
- Legal notice (Impressum): responsible body and a valid postal address (§ 5 TMG)
- Logo and image rights, and approval of the persons named
- `docs/assets/img/favicon.svg` is a placeholder graphic

Once `site_url` is set, the `social` plugin block in `mkdocs.yml`
(comment at `plugins`) can be re-enabled; it generates Open Graph cards and
requires the absolute URL.

## Deployment

`mkdocs gh-deploy` is prepared for GitHub Pages once a GitHub repository exists:

```bash
.venv/bin/mkdocs gh-deploy --force
```

For other hosting targets, simply serve the contents of `site/` as static files.

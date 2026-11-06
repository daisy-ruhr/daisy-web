# DAISY – Project Website

Static documentation site for the DAISY consortium
(*Datenschutz und Arbeitnehmendeninteressen in AI-as-a-Service-Systemen* – Data Protection
and Employee Interests in AI-as-a-Service Systems).
Built with [Zensical](https://zensical.org/) (successor to Material for MkDocs),
bilingual (German and English), without external JavaScript or CSS libraries – all assets
live in the repository, and no Google Fonts or CDN resources are loaded.

## Development

The Python environment lives in `.venv/` (not checked in). Python 3.11 or newer is required.

```bash
python3 -m venv .venv            # once, if the environment is missing
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/site.py serve
```

This builds and previews both languages at http://127.0.0.1:8000/. The preview does not
reload automatically: stop and restart it after changes. Do not use `zensical serve` to
test the language switcher: it builds only one language and can clear the other language
from `site/`, resulting in 404s.

## Build

```bash
.venv/bin/python scripts/site.py build
```

The German and English static output ends up in `site/de/` and `site/en/`, respectively
(see `.gitignore`).

## Languages

The German and English sites are built separately from their respective folders:

- `docs/de/` – German (served at `/de/`)
- `docs/en/` – English (served at `/en/`)

Visitors to `/` are sent to the first German or English language in their browser's
preferred-language list; English is the fallback if neither is supported. This selection
only runs at the root, so directly visiting or switching to a language is respected.
Without JavaScript, the root page offers links to both languages. Existing German page
URLs such as `/results/` redirect to `/de/results/`; these static redirects preserve
query strings and fragments when JavaScript is enabled. Hosts may optionally replace
them with permanent server-side redirects.

The [Zensical language selector](https://zensical.org/docs/setup/language/#site-language-selector)
links to existing translated sites; it does not build the translated content. This project
stores German settings and English overrides in `zensical.toml`. The build script derives a
temporary English configuration from those settings, builds each language, and combines
their sitemaps. Both builds inherit the same theme and extension settings.

Both folders must use the same file names so the language switcher can map each page to its
translation. Links between pages are relative (e.g. `project.md`), so they stay within the
current language. The build script copies the shared repository-level `assets/` directory
into each language's output.
The translated navigation and metadata are in `zensical.toml` under
`[project.extra.localization.en]`.

## Maintaining pages

| Task | Location |
| --- | --- |
| German navigation, metadata, and shared theme options | `zensical.toml` |
| English navigation and metadata | `zensical.toml`, under `[project.extra.localization.en]` |
| Content | `docs/de/*.md` (German), `docs/en/*.md` (English) – same file names in both folders |
| Colors, hero banner, special blocks | `assets/styles/extra.css` |
| Images and favicon | `assets/img/` |

Markdown extensions in use: admonitions (`!!!`), collapsible blocks (`???`),
tabs (`=== "Tab"`), grid cards (`<div class="grid cards" markdown="1">`),
definition lists (`def_list`), `attr_list` and `md_in_html`.

## To clarify before publishing

The site deliberately contains placeholders that must be replaced before going live:

- `site_url` in `zensical.toml` (domain, ending in `/de/`)
- Contact e-mail in `docs/*/contact.md` (currently `steffen.becker@rub.de`)
- Legal notice (Impressum): responsible body and a valid postal address (§ 5 TMG)
- Logo and image rights, and approval of the persons named
- `assets/img/favicon.svg` is a placeholder graphic

## Deployment

Zensical generates static files but does not deploy them. Publish the contents of `site/`
with the hosting provider of your choice.

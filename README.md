# DAISY – Project Website

Static documentation site for the DAISY consortium
(*Datenschutz und Arbeitnehmendeninteressen in AI-as-a-Service-Systemen* – Data Protection
and Employee Interests in AI-as-a-Service Systems).
Built with [Zensical](https://zensical.org/) (successor to Material for MkDocs),
bilingual (German and English), without external JavaScript or CSS libraries – all assets
live in the repository, and no Google Fonts or CDN resources are loaded.

## Development

The Python environment lives in `.venv/` (not checked in).

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

The German and English static output ends up in `site/` and `site/en/`, respectively
(see `.gitignore`).

## Languages

The German and English sites are built separately from their respective folders:

- `docs/de/` – German (default language, served at the site root `/`)
- `docs/en/` – English (served at `/en/`)

The [Zensical language selector](https://zensical.org/docs/setup/language/#site-language-selector)
links to existing translated sites; it does not build the translated content. This project
uses two configurations so each build has its own language, navigation, and metadata.
The build command above runs both configurations and combines their sitemaps.

Both folders must use the same file names so the language switcher can map each page to its
translation. Links between pages are relative (e.g. `project.md`), so they stay within the
current language. Both language folders link their `assets/` directory to the shared
repository-level `assets/` directory. Both Zensical configurations watch that directory so
its files are included in each build. Checkouts must preserve symbolic links.
The corresponding Zensical settings and translated navigation are in `zensical.toml` and
`zensical.en.toml`.

## Maintaining pages

| Task | Location |
| --- | --- |
| German navigation and theme options | `zensical.toml` |
| English navigation and theme options | `zensical.en.toml` |
| Content | `docs/de/*.md` (German), `docs/en/*.md` (English) – same file names in both folders |
| Colors, hero banner, special blocks | `assets/styles/extra.css` |
| Images and favicon | `assets/img/` |

Keep both language configurations in sync when changing shared theme settings.

Markdown extensions in use: admonitions (`!!!`), collapsible blocks (`???`),
tabs (`=== "Tab"`), grid cards (`<div class="grid cards" markdown="1">`),
definition lists (`def_list`), `attr_list` and `md_in_html`.

## To clarify before publishing

The site deliberately contains placeholders that must be replaced before going live:

- `site_url` in `zensical.toml` and `zensical.en.toml` (domain)
- Contact e-mail in `docs/*/contact.md` (currently `steffen.becker@rub.de`)
- Legal notice (Impressum): responsible body and a valid postal address (§ 5 TMG)
- Logo and image rights, and approval of the persons named
- `assets/img/favicon.svg` is a placeholder graphic

## Deployment

Zensical generates static files but does not deploy them. Publish the contents of `site/`
with the hosting provider of your choice.

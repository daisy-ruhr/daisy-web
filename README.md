# DAISY – Project Website

Static documentation site for the DAISY consortium
(*Datenschutz und Arbeitnehmendeninteressen in AI-as-a-Service-Systemen* – Data Protection
and Employee Interests in AI-as-a-Service Systems).
Built with [Zensical](https://zensical.org/) (successor to Material for MkDocs),
bilingual (German and English), without external JavaScript or CSS libraries – all assets
live in the repository, and no Google Fonts or CDN resources are loaded.

## Editing

The Python environment lives in `.venv/` (not checked in). Python 3.11 or newer is required.

```bash
python3 -m venv .venv            # once, if the environment is missing
.venv/bin/pip install -r requirements.txt
# German preview
.venv/bin/zensical serve

# English preview (in another terminal, with a different port)
.venv/bin/zensical serve --config-file zensical.en.toml --dev-addr 127.0.0.1:8001
```

The native preview rebuilds and reloads the browser after changes. Open the German site
at http://127.0.0.1:8000/de/ and the English site at http://127.0.0.1:8001/en/. Each server
serves only its own language, so the language switcher and root language selection cannot
be tested there. To preview both languages together, run the production build below, then
serve `site/` with `.venv/bin/python -m http.server --directory site 8000`; that static
preview does not reload automatically.

## Build

```bash
.venv/bin/zensical build --strict
.venv/bin/zensical build --config-file zensical.en.toml --strict
.venv/bin/python scripts/merge_sitemaps.py
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
uses `zensical.toml` and `zensical.en.toml` to build each language with its own navigation
and metadata. The final script combines the sitemaps and generates the root language
selector and legacy redirects. Keep shared theme and extension settings synchronized.

Both folders must use the same file names so the language switcher can map each page to its
translation. Links between pages are relative (e.g. `project.md`), so they stay within the
current language. All images and styles live in `overrides/assets/` and are included in
both builds by Zensical's theme override directory. In Markdown, use paths such as
`assets/img/daisy_staff.webp` or `assets/img/bmftr_de.png`.

## Maintaining pages

| Task | Location |
| --- | --- |
| German navigation, metadata, and shared theme options | `zensical.toml` |
| English navigation and metadata | `zensical.en.toml` |
| Content | `docs/de/*.md` (German), `docs/en/*.md` (English) – same file names in both folders |
| Colors, home page intro, special blocks | `overrides/assets/styles/extra.css` |
| Images and favicon | `overrides/assets/img/` |

Markdown extensions in use: admonitions (`!!!`), collapsible blocks (`???`),
tabs (`=== "Tab"`), grid cards (`<div class="grid cards" markdown="1">`),
definition lists (`def_list`), `attr_list`, `md_in_html`, and snippets (`--8<--`).

Currenty disabled pages are listed in `draft_docs` in each .toml file. These are excluded from the build and have also been disabled in the nav manually.
Files named `*.draft.md` match that pattern; the tests and the legacy redirect script skip them as well.

### Publications/Results

Edit `docs/shared/publications.md` once to update both language versions. The localized
introductions are in `docs/de/publications.md` and `docs/en/publications.md`. The page
lists all results (publications, talks, workshops, PoCs/code) chronologically under year
headings. The shared file contains commented-out examples for every type; copy the
matching one, replace the placeholder details and links with the real ones, and place it
under its year heading outside the comment. Each entry is a
`<div class="daisy-result" data-type="…" lang="…" markdown="1">` where `data-type` is
`publication`, `talk`, `workshop`, or `code`, followed by the matching filled type label
(`daisy-result-type`, which contains both a German and an English text; only the one
matching the page language is shown).

`overrides/assets/javascripts/results.js` adds filter buttons by type above the list once
it contains at least two types. It hides year headings and table-of-contents entries that
no longer have visible entries, hides the type labels while a single type is selected, and keeps the selection in the URL (e.g.
`publications/?type=talk`), so filtered views can be linked. Without JavaScript all
entries are shown. To add a type, extend `TYPES` and both label sets in that script.

Keep titles and authors in their original language, list entries newest first, and
use one or more of the `Computer Security`, `Psychology`, and `Human-Computer Interaction` labels.
Add the corresponding `cs`, `psy`, or `hci` CSS class alongside
`daisy-publication-tag` to color each label, as shown in the examples.
DOI buttons should link to the corresponding `https://doi.org/` URL. The examples are
not real publications. Changes to the shared file are watched by the preview servers.

### News

The Zensical blog builds the news overview at `/de/news/` and `/en/news/` in reverse
chronological order. To add a post, create matching Markdown files under
`docs/de/news/posts/` and `docs/en/news/posts/`. Give both versions the same `date`
(`YYYY-MM-DD`) and explicit, URL-safe `slug` in their front matter; the shared slug is
necessary for language switching. Use a unique slug for each article, and keep it stable
after publication. Add `<!-- more -->` after the introduction to set the overview excerpt.
Individual posts must not be added to navigation. Set `draft: true` in both versions to
preview a post without publishing it, then remove it from both versions when ready.

The home page loads up to three posts from the generated news overview, so it stays in
sync with the blog without maintaining a separate list. This requires JavaScript and an
HTTP server (including Zensical's preview); the link to all news remains available
without JavaScript.

### Team

Use the following template to add a new person within the `daisy-people` div of the correct org.
Ensure that both the German and English pages are updated in sync.

```html
<div class="daisy-person" markdown="1">
<div class="daisy-person-text" markdown="1">

#### Maria Mustermann

<p class="daisy-person-role">Awesomeness Manager</p>

I am responsible for making DAISY a full success! Replace me with your actual bio.

</div>
<!-- following line is optional, only needed if photo is present. Filename pattern GivenName_Surname.JPG -->
<div class="daisy-person-photo"><img src="assets/img/staff/Maria_Mustermann.JPG" alt="" loading="lazy"></div>
</div>
```

Also update `docs/shared/team-icons.html`, which supplies the icon bar below the partner
logos on both home pages. Keep the icons in the same order as the team pages. Give each
link the matching `daisy-org-*` class from `docs/shared/partner-logos.html`, the person's
name as its `aria-label`, and a `team/#...` link to the heading's generated ID on both
team pages. Add a `daisy-team-tooltip` span with `aria-hidden="true"` and the same name,
wrapping each word in a separate `span` so names only wrap at spaces. Use a photo from `assets/img/staff/` with an empty `alt`, or a
`<span aria-hidden="true">` containing initials until a photo is available. Replace the
placeholder when the photo is added. The icon bar's minimum size can be changed with
`--team-icon-min-size` in `overrides/assets/styles/extra.css`; icons wrap into more rows
when they no longer fit.

## Accessibility

The site targets WCAG 2.1 AA (BITV 2.0 / EN 301 549). When editing content:

- Use real headings (`##`, `###`) instead of bold lines, without skipping levels.
- Give every informative image an `alt` text; use `alt=""` only for decorative images
  (e.g. team photos next to the person's name).
- Mark passages in the other language, e.g. `<span lang="en">Human Factors</span>` on German
  pages; in `docs/shared/publications.md` wrap each entry in `<div lang="..." markdown="1">`.
- Use descriptive link texts.
- Check colour contrast (4.5:1 for text, 3:1 for icons/borders) in both light and dark mode.

### Automated check

CI runs [axe-core](https://github.com/dequelabs/axe-core) on every page of the built site in
light and dark mode at 1280px and 320px width. WCAG 2.0/2.1/2.2 A and AA violations fail the
build; axe best-practice findings are only reported as warnings. To run it locally after the
build (requires Node.js and Chrome or Chromium; set `CHROME_PATH` if it is not found):

```bash
npm ci --prefix tests/a11y
node tests/a11y/axe.mjs
```

Automated checks find only part of the barriers. Keyboard, screen reader and zoom tests
still have to be done manually.

### Accessibility statement

The *Erklärung zur Barrierefreiheit* is drafted in `docs/de/Barrierefreiheit.draft.md` and
`docs/en/Barrierefreiheit.draft.md` (status: partially compliant). To publish it:

1. Replace every `[TODO: …]` placeholder in both files (responsible body, contact, dates,
   enforcement body, legal basis, results of the manual review) and remove the draft comment.
2. Rename both files to `Barrierefreiheit.md` (same name in both languages, like `Impressum.md`).
3. Add a footer link next to Impressum/Datenschutz in `overrides/main.html`, e.g.
   `<a href="/{{ config.theme.language }}/Barrierefreiheit/">{{ 'Accessibility' if en else 'Barrierefreiheit' }}</a>`.
4. Review the statement at least once a year and after major changes, and update its date.

## Deployment

Zensical generates static files but does not deploy them. Publish the contents of `site/`
with the hosting provider of your choice.

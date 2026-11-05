# DAISY – Projektdokumentation

Statische Dokumentationsseite für den DAISY-Verbund
(*Datenschutz und Arbeitnehmendeninteressen in AI-as-a-Service-Systemen*).
Erzeugt mit [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/),
auf Deutsch, ohne externe JavaScript- oder CSS-Bibliotheken – alle Assets liegen im
Repository, es werden keine Google Fonts und keine CDN-Ressourcen geladen.

## Entwicklung

Die Python-Umgebung liegt in `.venv/` (nicht eingecheckt).

```bash
python3 -m venv .venv            # einmalig, falls die Umgebung fehlt
.venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve           # Live-Preview auf http://127.0.0.1:8000
```

Hinweis: `source .venv/bin/activate` wirkt nur in der Shell, in der es ausgeführt
wird. In Skripten und CI besser direkt `.venv/bin/mkdocs` aufrufen.

## Build

```bash
.venv/bin/mkdocs build --strict   # bricht bei toten Links und Warnungen ab
```

Die statische Ausgabe landet in `site/` (`.gitignore`).

## Seiten pflegen

| Aufgabe | Ort |
| --- | --- |
| Navigation und Theme-Optionen | `mkdocs.yml` |
| Inhalte | `docs/*.md` |
| Farben, Hero-Banner, Sonderblöcke | `docs/assets/styles/extra.css` |
| Bilder und Favicon | `docs/assets/img/` |

Beim Bearbeiten von `mkdocs.yml` oder `extra.css` die Vorschau neu laden; `mkdocs serve`
übernimmt Änderungen automatisch.

Verwendete Markdown-Erweiterungen: Admonitions (`!!!`), kollabierbare Blöcke (`???`),
Tabs (`=== "Reiter"`), Grid Cards (`<div class="grid cards" markdown="1">`),
Definitionen (`def_list`), `attr_list` und `md_in_html`.

## Vor dem Veröffentlichen klären

Die Seite enthält bewusst Platzhalter, die vor dem Live-Gang ersetzt werden müssen:

- `site_url` und `repo_url` in `mkdocs.yml` (Domain und Repository-URL)
- Kontakt-E-Mail in `mkdocs.yml` und `docs/kontakt.md` (derzeit `steffen.becker@rub.de`)
- Impressum: verantwortliche Stelle und ladungsfähige Anschrift (§ 5 TMG)
- Logo- und Bildrechte sowie Freigabe der genannten Personen
- `docs/assets/img/favicon.svg` ist eine Platzhaltergrafik

Ist `site_url` gesetzt, kann der `social`-Plugin-Block in `mkdocs.yml`
(Kommentar bei `plugins`) wieder aktiviert werden; er erzeugt Open-Graph-Cards und
benötigt die absolute URL.

## Deployment

`mkdocs gh-deploy` ist für GitHub Pages vorbereitet, sobald ein GitHub-Repository
existiert:

```bash
.venv/bin/mkdocs gh-deploy --force
```

Für andere Hosting-Ziele einfach den Inhalt von `site/` als statische Dateien
ausliefern.

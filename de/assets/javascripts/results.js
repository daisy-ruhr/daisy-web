// Type filter for the results page. Without JavaScript all entries stay visible.
document.addEventListener("DOMContentLoaded", () => {
  const container = document.querySelector(".daisy-publications");
  if (!container) return;

  const TYPES = ["publication", "talk", "workshop", "code"];
  const TEXT = {
    de: {
      group: "Ergebnisse nach Typ filtern",
      all: "Alle",
      publication: "Publikationen",
      talk: "Vorträge",
      workshop: "Workshops",
      code: "PoCs / Code",
      status: (n) => (n === 1 ? "1 Eintrag angezeigt" : `${n} Einträge angezeigt`),
    },
    en: {
      group: "Filter results by type",
      all: "All",
      publication: "Publications",
      talk: "Talks",
      workshop: "Workshops",
      code: "PoCs / Code",
      status: (n) => (n === 1 ? "Showing 1 entry" : `Showing ${n} entries`),
    },
  }[document.documentElement.lang.startsWith("de") ? "de" : "en"];

  // Group entries by the year heading (h2) that precedes them.
  const sections = [];
  const entries = [];
  for (const child of container.children) {
    if (child.tagName === "H2") {
      sections.push({ heading: child, entries: [] });
    } else if (child.matches(".daisy-result[data-type]")) {
      entries.push(child);
      if (sections.length) sections[sections.length - 1].entries.push(child);
    }
  }

  const counts = new Map();
  for (const entry of entries) counts.set(entry.dataset.type, (counts.get(entry.dataset.type) || 0) + 1);
  const types = TYPES.filter((type) => counts.has(type));
  // A filter only helps once there is more than one kind of result.
  if (types.length < 2) return;

  // Hide the table-of-contents link of a hidden heading as well.
  const tocItem = (heading) => {
    if (!heading?.id) return [];
    return Array.from(document.querySelectorAll(".md-nav--secondary a.md-nav__link"))
      .filter((link) => link.getAttribute("href") === `#${heading.id}`)
      .map((link) => link.closest("li"));
  };

  const toolbar = document.createElement("div");
  toolbar.className = "daisy-filter";
  const group = document.createElement("div");
  group.className = "daisy-filter__chips";
  group.setAttribute("role", "group");
  group.setAttribute("aria-label", TEXT.group);
  const status = document.createElement("p");
  status.className = "daisy-filter__status";
  status.setAttribute("role", "status");

  const buttons = new Map();
  for (const type of ["all", ...types]) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "daisy-filter__chip";
    button.dataset.type = type;
    const label = document.createElement("span");
    label.textContent = TEXT[type];
    const count = document.createElement("span");
    count.className = "daisy-filter__count";
    count.textContent = type === "all" ? entries.length : counts.get(type);
    button.append(label, " ", count);
    button.addEventListener("click", () => apply(type, true));
    buttons.set(type, button);
    group.append(button);
  }
  toolbar.append(group, status);
  container.before(toolbar);

  function apply(type, updateUrl) {
    let shown = 0;
    for (const entry of entries) {
      const hidden = type !== "all" && entry.dataset.type !== type;
      entry.hidden = hidden;
      tocItem(entry.querySelector("h3[id]")).forEach((item) => { item.hidden = hidden; });
      if (!hidden) shown += 1;
    }
    for (const section of sections) {
      if (!section.entries.length) continue;
      const hidden = section.entries.every((entry) => entry.hidden);
      section.heading.hidden = hidden;
      tocItem(section.heading).forEach((item) => { item.hidden = hidden; });
    }
    // With a single type selected, the type label on every entry would be redundant.
    container.classList.toggle("daisy-publications--filtered", type !== "all");
    for (const [key, button] of buttons) button.setAttribute("aria-pressed", String(key === type));
    status.textContent = TEXT.status(shown);

    if (updateUrl) {
      const url = new URL(window.location.href);
      if (type === "all") url.searchParams.delete("type");
      else url.searchParams.set("type", type);
      history.replaceState(history.state, "", url);
    }
  }

  const requested = new URLSearchParams(window.location.search).get("type");
  apply(types.includes(requested) ? requested : "all", false);
});

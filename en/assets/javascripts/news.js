document.addEventListener("DOMContentLoaded", () => {
  const container = document.querySelector(".daisy-latest-news");
  if (!container) return;

  const overviewUrl = new URL(container.dataset.newsUrl, document.baseURI);
  const done = () => container.setAttribute("aria-busy", "false");
  fetch(overviewUrl)
    .then((response) => {
      if (!response.ok) throw new Error(`News request failed: ${response.status}`);
      return response.text();
    })
    .then((html) => {
      const overview = new DOMParser().parseFromString(html, "text/html");
      const posts = Array.from(overview.querySelectorAll(".md-post--excerpt")).slice(0, 3);
      if (!overview.querySelector(".md-content")) throw new Error("Invalid news overview");
      if (!posts.length) {
        container.textContent = container.dataset.newsEmpty;
        return;
      }
      const list = document.createElement("ul");
      for (const post of posts) {
        const title = post.querySelector(".md-post__content h2 a[href]");
        const date = post.querySelector("time[datetime]");
        if (!title || !date) throw new Error("Invalid news post");
        const item = document.createElement("li");
        const time = document.createElement("time");
        time.dateTime = date.getAttribute("datetime");
        time.textContent = date.textContent.trim();
        const link = document.createElement("a");
        link.href = new URL(title.getAttribute("href"), overviewUrl).href;
        link.textContent = title.textContent.trim();
        item.append(time, link);
        list.append(item);
      }
      container.replaceChildren(list);
    })
    .catch((error) => {
      console.error("Could not load latest news:", error);
      container.textContent = container.dataset.newsError;
    })
    .finally(done);
});

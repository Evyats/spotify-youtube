(function () {
  const { api, showToast, requireAuth, renderAuthState } = window.App;
  const byId = (id) => document.getElementById(id);
  const list = byId("searchResults");

  function candidateToImportPayload(c) {
    return {
      source_provider: c.source_provider || "youtube",
      source_id: c.source_id,
      title: c.title,
      artist: c.channel || "Unknown",
      candidate_meta: c,
    };
  }

  function renderResults(data) {
    const candidates = data?.candidates || [];
    if (candidates.length === 0) {
      list.innerHTML = '<p class="hint">No results found.</p>';
      return;
    }

    list.innerHTML = "";
    candidates.forEach((c, idx) => {
      const item = document.createElement("article");
      item.className = "item";
      item.innerHTML = `
        <div class="item-title">${idx + 1}. ${c.title || "Untitled"}</div>
        <div class="item-meta">${c.channel || "Unknown"} | score ${typeof c.confidence_score === "number" ? c.confidence_score.toFixed(3) : "n/a"}</div>
        <div class="row">
          <button class="add-btn">Add to Library</button>
          <button class="open-btn secondary">Open on YouTube</button>
        </div>
      `;
      item.querySelector(".add-btn").addEventListener("click", async () => {
        if (!requireAuth()) return;
        try {
          await api("/songs/import", {
            method: "POST",
            body: JSON.stringify(candidateToImportPayload(c)),
          });
          showToast("Song import started.");
        } catch (err) {
          showToast(err.message);
        }
      });
      item.querySelector(".open-btn").addEventListener("click", () => {
        if (!c.source_id) return;
        window.open(`https://www.youtube.com/watch?v=${encodeURIComponent(c.source_id)}`, "_blank", "noopener,noreferrer");
      });
      list.appendChild(item);
    });
  }

  byId("searchBtn")?.addEventListener("click", async () => {
    if (!requireAuth()) return;
    try {
      const q = encodeURIComponent(byId("query").value.trim());
      const data = await api(`/songs/search?q=${q}`);
      renderResults(data);
    } catch (err) {
      showToast(err.message);
    }
  });

  renderAuthState();
})();

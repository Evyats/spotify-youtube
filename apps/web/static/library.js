(function () {
  const { api, showToast, requireAuth, renderAuthState } = window.App;
  const byId = (id) => document.getElementById(id);
  const list = byId("libraryList");
  const player = byId("player");
  const nowPlaying = byId("nowPlaying");

  async function loadLibrary() {
    if (!requireAuth()) return;
    const data = await api("/library");
    const songs = data?.songs || [];
    if (songs.length === 0) {
      list.innerHTML = '<p class="hint">Library is empty.</p>';
      return;
    }

    list.innerHTML = "";
    songs.forEach((song) => {
      const item = document.createElement("article");
      item.className = "item";
      item.innerHTML = `
        <div class="item-title">${song.title || "Untitled"}</div>
        <div class="item-meta">${song.artist || "Unknown artist"}</div>
        <button class="play-btn">Play</button>
      `;
      item.querySelector(".play-btn").addEventListener("click", async () => {
        try {
          const res = await api(`/stream/${song.id}`);
          if (!res?.stream_url) throw new Error("Missing stream URL");
          player.src = res.stream_url;
          nowPlaying.textContent = `${song.title} - ${song.artist}`;
          await player.play();
        } catch (err) {
          showToast(err.message);
        }
      });
      list.appendChild(item);
    });
  }

  byId("libraryBtn")?.addEventListener("click", async () => {
    try {
      await loadLibrary();
    } catch (err) {
      showToast(err.message);
    }
  });

  renderAuthState();
  loadLibrary().catch(() => {});
})();

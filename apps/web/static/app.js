(function () {
  const API = window.APP_CONFIG?.apiBase || "http://localhost:8000";
  const byId = (id) => document.getElementById(id);

  const authState = byId("authState");
  const searchResults = byId("searchResults");
  const libraryList = byId("libraryList");
  const nowPlaying = byId("nowPlaying");
  const player = byId("player");
  const toast = byId("toast");

  let accessToken = localStorage.getItem("access_token") || "";

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.remove("hidden");
    setTimeout(() => toast.classList.add("hidden"), 2400);
  }

  function isSignedIn() {
    return accessToken.length > 0;
  }

  function refreshAuthState() {
    authState.textContent = isSignedIn() ? "Signed in" : "Not signed in";
  }

  async function api(path, init = {}) {
    const headers = { "Content-Type": "application/json", ...(init.headers || {}) };
    if (isSignedIn()) headers.Authorization = `Bearer ${accessToken}`;

    const res = await fetch(`${API}${path}`, { ...init, headers });
    const text = await res.text();
    let data = text;
    try {
      data = JSON.parse(text);
    } catch {}
    if (!res.ok) {
      const detail = data?.detail || data || `Request failed (${res.status})`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return data;
  }

  function requireAuth() {
    if (!isSignedIn()) {
      showToast("Sign in first.");
      return false;
    }
    return true;
  }

  function candidateToImportPayload(c) {
    return {
      source_provider: c.source_provider || "youtube",
      source_id: c.source_id,
      title: c.title,
      artist: c.channel || "Unknown",
      candidate_meta: c,
    };
  }

  function renderSearchResults(data) {
    const candidates = data?.candidates || [];
    if (candidates.length === 0) {
      searchResults.innerHTML = '<p class="hint">No results found.</p>';
      return;
    }

    searchResults.innerHTML = "";
    candidates.forEach((c, idx) => {
      const item = document.createElement("article");
      item.className = "item";
      item.innerHTML = `
        <div class="item-title">${idx + 1}. ${c.title || "Untitled"}</div>
        <div class="item-meta">${c.channel || "Unknown"} · score ${typeof c.confidence_score === "number" ? c.confidence_score.toFixed(3) : "n/a"}</div>
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
          await loadLibrary();
        } catch (err) {
          showToast(err.message);
        }
      });
      item.querySelector(".open-btn").addEventListener("click", () => {
        const sourceId = c.source_id;
        if (!sourceId) {
          showToast("Missing YouTube source id.");
          return;
        }
        window.open(`https://www.youtube.com/watch?v=${encodeURIComponent(sourceId)}`, "_blank", "noopener,noreferrer");
      });
      searchResults.appendChild(item);
    });
  }

  async function loadLibrary() {
    if (!requireAuth()) return;
    const data = await api("/library");
    const songs = data?.songs || [];
    if (songs.length === 0) {
      libraryList.innerHTML = '<p class="hint">Library is empty.</p>';
      return;
    }

    libraryList.innerHTML = "";
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
      libraryList.appendChild(item);
    });
  }

  byId("signupBtn").addEventListener("click", async () => {
    try {
      const email = byId("email").value.trim();
      const password = byId("password").value;
      const data = await api("/auth/signup", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      if (data.verification_token) byId("verifyToken").value = data.verification_token;
      showToast("Signup complete. Verify email, then sign in.");
    } catch (err) {
      showToast(err.message);
    }
  });

  byId("verifyBtn").addEventListener("click", async () => {
    try {
      const token = byId("verifyToken").value.trim();
      await api("/auth/verify-email", {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      showToast("Email verified.");
    } catch (err) {
      showToast(err.message);
    }
  });

  byId("signinBtn").addEventListener("click", async () => {
    try {
      const email = byId("email").value.trim();
      const password = byId("password").value;
      const data = await api("/auth/signin", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      accessToken = data.access_token || "";
      localStorage.setItem("access_token", accessToken);
      refreshAuthState();
      showToast("Signed in.");
      await loadLibrary();
    } catch (err) {
      showToast(err.message);
    }
  });

  byId("searchBtn").addEventListener("click", async () => {
    if (!requireAuth()) return;
    try {
      const q = encodeURIComponent(byId("query").value.trim());
      const data = await api(`/songs/search?q=${q}`);
      renderSearchResults(data);
    } catch (err) {
      showToast(err.message);
    }
  });

  byId("libraryBtn").addEventListener("click", async () => {
    try {
      await loadLibrary();
    } catch (err) {
      showToast(err.message);
    }
  });

  refreshAuthState();
})();

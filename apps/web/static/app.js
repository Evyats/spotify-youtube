(function () {
  const API = window.APP_CONFIG?.apiBase || "http://localhost:8000";

  const byId = (id) => document.getElementById(id);
  const output = byId("output");
  const resultsList = byId("resultsList");

  function token() {
    return byId("accessToken").value.trim();
  }

  function setOutput(data) {
    output.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  }

  function renderResults(data) {
    if (!data || !Array.isArray(data.candidates) || data.candidates.length === 0) {
      resultsList.innerHTML = '<p class="muted">No candidates returned.</p>';
      return;
    }

    resultsList.innerHTML = data.candidates
      .map(
        (c, idx) => `
        <article class="result-item">
          <h3>${idx + 1}. ${c.title || "Untitled"}</h3>
          <div class="result-meta">Channel: ${c.channel || "Unknown"} | Source: ${c.source_id || "n/a"} | Score: ${typeof c.confidence_score === "number" ? c.confidence_score.toFixed(3) : "n/a"}</div>
        </article>
      `
      )
      .join("");
  }

  async function api(path, init = {}) {
    const headers = Object.assign(
      { "Content-Type": "application/json" },
      init.headers || {},
      token() ? { Authorization: `Bearer ${token()}` } : {}
    );
    const res = await fetch(`${API}${path}`, { ...init, headers });
    const text = await res.text();
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
    if (!res.ok) {
      throw { status: res.status, data };
    }
    return data;
  }

  async function handle(action) {
    try {
      const result = await action();
      setOutput(result);
    } catch (err) {
      setOutput({ error: true, detail: err.data || err.message || err, status: err.status || 500 });
    }
  }

  byId("signupBtn").addEventListener("click", () =>
    handle(async () => {
      return api("/auth/signup", {
        method: "POST",
        body: JSON.stringify({
          email: byId("email").value.trim(),
          password: byId("password").value,
        }),
      });
    })
  );

  byId("verifyBtn").addEventListener("click", () =>
    handle(async () => {
      return api("/auth/verify-email", {
        method: "POST",
        body: JSON.stringify({ token: byId("verifyToken").value.trim() }),
      });
    })
  );

  byId("signinBtn").addEventListener("click", () =>
    handle(async () => {
      const data = await api("/auth/signin", {
        method: "POST",
        body: JSON.stringify({
          email: byId("email").value.trim(),
          password: byId("password").value,
        }),
      });
      if (data.access_token) byId("accessToken").value = data.access_token;
      return data;
    })
  );

  byId("searchBtn").addEventListener("click", () =>
    handle(async () => {
      const q = encodeURIComponent(byId("query").value.trim());
      const data = await api(`/songs/search?q=${q}`);
      renderResults(data);
      if (data.candidates?.[0]) {
        byId("candidateJson").value = JSON.stringify(
          {
            source_provider: data.candidates[0].source_provider,
            source_id: data.candidates[0].source_id,
            title: data.candidates[0].title,
            artist: data.candidates[0].channel,
            candidate_meta: data.candidates[0],
          },
          null,
          2
        );
      }
      return data;
    })
  );

  byId("libraryBtn").addEventListener("click", () => handle(() => api("/library")));

  byId("importBtn").addEventListener("click", () =>
    handle(async () => {
      let payload = {};
      try {
        payload = JSON.parse(byId("candidateJson").value || "{}");
      } catch {
        throw new Error("candidate JSON is invalid");
      }
      return api("/songs/import", { method: "POST", body: JSON.stringify(payload) });
    })
  );

  byId("clearOutputBtn").addEventListener("click", () => {
    setOutput('{ "ready": true }');
    renderResults({ candidates: [] });
  });
})();

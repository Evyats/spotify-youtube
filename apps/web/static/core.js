(function () {
  const API = window.APP_CONFIG?.apiBase || "http://localhost:8000";
  const toast = document.getElementById("toast");

  function showToast(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.remove("hidden");
    setTimeout(() => toast.classList.add("hidden"), 2200);
  }

  function getToken() {
    return localStorage.getItem("access_token") || "";
  }

  function getSessionEmail() {
    return localStorage.getItem("session_email") || "";
  }

  function setSessionEmail(email) {
    if (!email) {
      localStorage.removeItem("session_email");
      return;
    }
    localStorage.setItem("session_email", email);
  }

  function setToken(token) {
    if (!token) {
      localStorage.removeItem("access_token");
      setSessionEmail("");
      return;
    }
    localStorage.setItem("access_token", token);
  }

  function isSignedIn() {
    return getToken().length > 0;
  }

  function renderAuthState() {
    const el = document.getElementById("authState");
    if (el) el.textContent = isSignedIn() ? "Signed in" : "Not signed in";

    const topEl = document.getElementById("signedInAs");
    if (topEl) {
      const email = getSessionEmail();
      topEl.textContent = isSignedIn() ? `Signed in as ${email || "current user"}` : "Signed out";
    }
  }

  async function api(path, init = {}) {
    const headers = Object.assign({ "Content-Type": "application/json" }, init.headers || {});
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;

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

  window.App = {
    api,
    showToast,
    getToken,
    setToken,
    getSessionEmail,
    setSessionEmail,
    isSignedIn,
    requireAuth,
    renderAuthState,
  };

  renderAuthState();
})();

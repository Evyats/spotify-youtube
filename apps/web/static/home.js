(function () {
  const { api, showToast, setToken, setSessionEmail, renderAuthState } = window.App;
  const byId = (id) => document.getElementById(id);

  byId("signupBtn")?.addEventListener("click", async () => {
    try {
      const data = await api("/auth/signup", {
        method: "POST",
        body: JSON.stringify({
          email: byId("email").value.trim(),
          password: byId("password").value,
        }),
      });
      if (data.verification_token) byId("verifyToken").value = data.verification_token;
      showToast("Signup complete.");
    } catch (err) {
      showToast(err.message);
    }
  });

  byId("verifyBtn")?.addEventListener("click", async () => {
    try {
      await api("/auth/verify-email", {
        method: "POST",
        body: JSON.stringify({ token: byId("verifyToken").value.trim() }),
      });
      showToast("Email verified.");
    } catch (err) {
      showToast(err.message);
    }
  });

  byId("signinBtn")?.addEventListener("click", async () => {
    try {
      const data = await api("/auth/signin", {
        method: "POST",
        body: JSON.stringify({
          email: byId("email").value.trim(),
          password: byId("password").value,
        }),
      });
      setToken(data.access_token || "");
      setSessionEmail(byId("email").value.trim());
      renderAuthState();
      showToast("Signed in.");
    } catch (err) {
      showToast(err.message);
    }
  });

  byId("signoutBtn")?.addEventListener("click", () => {
    setToken("");
    setSessionEmail("");
    renderAuthState();
    showToast("Signed out.");
  });
})();

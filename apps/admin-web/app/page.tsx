"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function AdminPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [refreshToken, setRefreshToken] = useState("");
  const [authStatus, setAuthStatus] = useState("");
  const [output, setOutput] = useState("{}");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const savedAccess = window.localStorage.getItem("admin_access_token") ?? "";
    const savedRefresh = window.localStorage.getItem("admin_refresh_token") ?? "";
    setAccessToken(savedAccess);
    setRefreshToken(savedRefresh);
  }, []);

  const signedIn = useMemo(() => accessToken.length > 0, [accessToken]);

  async function call(path: string) {
    setLoading(true);
    try {
      const res = await fetch(`${API}${path}`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      const json = await res.json();
      setOutput(JSON.stringify(json, null, 2));
    } catch (error) {
      setOutput(JSON.stringify({ error: true, detail: String(error) }, null, 2));
    } finally {
      setLoading(false);
    }
  }

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setAuthStatus("Signing in...");
    setLoading(true);
    try {
      const res = await fetch(`${API}/auth/signin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const json = await res.json();
      if (!res.ok) {
        setAuthStatus(`Sign-in failed (${res.status})`);
        setOutput(JSON.stringify(json, null, 2));
        return;
      }
      const nextAccess = json.access_token ?? "";
      const nextRefresh = json.refresh_token ?? "";
      setAccessToken(nextAccess);
      setRefreshToken(nextRefresh);
      window.localStorage.setItem("admin_access_token", nextAccess);
      window.localStorage.setItem("admin_refresh_token", nextRefresh);
      setAuthStatus("Signed in successfully.");
      setOutput(JSON.stringify(json, null, 2));
    } catch (error) {
      setAuthStatus("Sign-in failed (network error).");
      setOutput(JSON.stringify({ error: true, detail: String(error) }, null, 2));
    } finally {
      setLoading(false);
    }
  }

  function signOut() {
    setAccessToken("");
    setRefreshToken("");
    setPassword("");
    setAuthStatus("Signed out.");
    window.localStorage.removeItem("admin_access_token");
    window.localStorage.removeItem("admin_refresh_token");
  }

  return (
    <main style={{ maxWidth: 960, margin: "0 auto", padding: "24px 16px", fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ marginBottom: 6 }}>Admin Panel</h1>
      <p style={{ marginTop: 0, color: "#334155" }}>Gateway: {API}</p>

      <section
        style={{
          border: "1px solid #d1d5db",
          borderRadius: 10,
          padding: 14,
          background: "#f8fafc",
          marginBottom: 16,
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 18 }}>Login</h2>
        <form onSubmit={signIn}>
          <div style={{ display: "grid", gap: 8 }}>
            <input
              type="email"
              placeholder="admin email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{ padding: "8px 10px" }}
            />
            <input
              type="password"
              placeholder="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              style={{ padding: "8px 10px" }}
            />
          </div>
          <div style={{ marginTop: 10, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <button type="submit" disabled={loading}>
              Sign In
            </button>
            <button type="button" onClick={signOut}>
              Sign Out
            </button>
            <span style={{ color: signedIn ? "#166534" : "#92400e" }}>
              {signedIn ? "Session active" : "No active session"}
            </span>
          </div>
          <div style={{ marginTop: 8, color: "#475569", fontSize: 14 }}>{authStatus}</div>
        </form>
      </section>

      <section
        style={{
          border: "1px solid #d1d5db",
          borderRadius: 10,
          padding: 14,
          background: "#f8fafc",
          marginBottom: 16,
        }}
      >
        <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 18 }}>Admin Data</h2>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button onClick={() => call("/admin/users")} disabled={!signedIn || loading}>
            Users
          </button>
          <button onClick={() => call("/admin/songs")} disabled={!signedIn || loading}>
            Songs
          </button>
          <button onClick={() => call("/admin/jobs")} disabled={!signedIn || loading}>
            Jobs
          </button>
          <button onClick={() => setOutput("{}")} disabled={loading}>
            Clear
          </button>
        </div>
        <p style={{ marginTop: 10, marginBottom: 0, color: "#475569", fontSize: 14 }}>
          Access token length: {accessToken.length} | Refresh token length: {refreshToken.length}
        </p>
      </section>

      <div>
        <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 18 }}>Response</h2>
        <pre
          style={{
            background: "#0b1220",
            color: "#e2e8f0",
            padding: 12,
            whiteSpace: "pre-wrap",
            marginTop: 0,
            borderRadius: 8,
            minHeight: 220,
          }}
        >
          {output}
        </pre>
      </div>
    </main>
  );
}

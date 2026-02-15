"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function AdminPage() {
  const [token, setToken] = useState("");
  const [output, setOutput] = useState("");

  async function call(path: string) {
    const res = await fetch(`${API}${path}`, { headers: { Authorization: `Bearer ${token}` } });
    const json = await res.json();
    setOutput(JSON.stringify(json, null, 2));
  }

  return (
    <main style={{ maxWidth: 920, margin: "0 auto" }}>
      <h1>Admin Web</h1>
      <p>Gateway: {API}</p>
      <input
        style={{ width: "100%" }}
        placeholder="admin bearer token"
        value={token}
        onChange={(e) => setToken(e.target.value)}
      />
      <div style={{ marginTop: 12 }}>
        <button onClick={() => call("/admin/users")}>Users</button>
        <button onClick={() => call("/admin/songs")} style={{ marginLeft: 8 }}>
          Songs
        </button>
        <button onClick={() => call("/admin/jobs")} style={{ marginLeft: 8 }}>
          Jobs
        </button>
      </div>
      <pre style={{ background: "#f3f3f3", padding: 12, whiteSpace: "pre-wrap", marginTop: 12 }}>{output}</pre>
    </main>
  );
}

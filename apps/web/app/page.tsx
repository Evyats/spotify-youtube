"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export default function Page() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [token, setToken] = useState("");
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<string>("");

  async function req(path: string, init?: RequestInit) {
    const res = await fetch(`${API}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(init?.headers || {}),
      },
    });
    const text = await res.text();
    let json: unknown = text;
    try {
      json = JSON.parse(text);
    } catch {
      // keep text
    }
    setResult(JSON.stringify(json, null, 2));
    return json;
  }

  return (
    <main style={{ maxWidth: 920, margin: "0 auto" }}>
      <h1>Spotify YouTube Web MVP</h1>
      <p>Gateway: {API}</p>

      <section>
        <h2>Auth</h2>
        <input placeholder="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <input placeholder="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button onClick={() => req("/auth/signup", { method: "POST", body: JSON.stringify({ email, password }) })}>Sign up</button>
        <button
          onClick={async () => {
            const json = (await req("/auth/signin", {
              method: "POST",
              body: JSON.stringify({ email, password }),
            })) as { access_token?: string };
            if (json?.access_token) setToken(json.access_token);
          }}
        >
          Sign in
        </button>
      </section>

      <section>
        <h2>Search + Library</h2>
        <input placeholder="song search" value={query} onChange={(e) => setQuery(e.target.value)} />
        <button onClick={() => req(`/songs/search?q=${encodeURIComponent(query)}`)}>Search</button>
        <button onClick={() => req("/library")}>Library</button>
      </section>

      <section>
        <h2>Result</h2>
        <pre style={{ background: "#f3f3f3", padding: 12, whiteSpace: "pre-wrap" }}>{result}</pre>
      </section>
    </main>
  );
}

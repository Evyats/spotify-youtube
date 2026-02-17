import { useState } from "react";
import ResponseViewer from "../components/ResponseViewer";
import type { AppHelpers } from "../App";

type HomePageProps = {
  helpers: AppHelpers;
  onSignIn: (email: string, password: string) => Promise<void>;
  onSignOut: () => Promise<void>;
  onSignedInEmail: (email: string) => void;
  responseText: string;
  clearResponse: () => void;
};

export default function HomePage({
  helpers,
  onSignIn,
  onSignOut,
  onSignedInEmail,
  responseText,
  clearResponse
}: HomePageProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [verifyToken, setVerifyToken] = useState("");

  async function signUp() {
    const data = await helpers.api("/auth/signup", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ email, password })
    });
    const token = (data as { verification_token?: string }).verification_token;
    if (token) setVerifyToken(token);
    helpers.setResponse(data);
    helpers.notify("Signup complete.");
  }

  async function verifyEmail() {
    const data = await helpers.api("/auth/verify-email", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ token: verifyToken })
    });
    helpers.setResponse(data);
    helpers.notify("Email verified.");
  }

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-slate-200 bg-panel p-4">
        <h2 className="mb-3 text-lg font-semibold">Account</h2>
        <div className="grid gap-2 md:grid-cols-2">
          <input
            className="input"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
          />
          <input
            className="input"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
          />
        </div>
        <div className="mt-3 flex flex-wrap gap-2">
          <button className="btn-primary" onClick={() => signUp().catch((e) => helpers.notify(e.message))}>
            Sign Up
          </button>
          <button className="btn-secondary" onClick={() => verifyEmail().catch((e) => helpers.notify(e.message))}>
            Verify
          </button>
          <button
            className="btn-secondary"
            onClick={() =>
              onSignIn(email.trim(), password)
                .then(() => onSignedInEmail(email.trim()))
                .catch((e) => helpers.notify(e.message))
            }
          >
            Sign In
          </button>
          <button className="btn-secondary" onClick={() => onSignOut().catch((e) => helpers.notify(e.message))}>
            Sign Out
          </button>
        </div>
        <input
          className="input mt-3"
          placeholder="Verification token (optional in dev)"
          value={verifyToken}
          onChange={(e) => setVerifyToken(e.target.value)}
        />
      </section>

      <section className="rounded-xl border border-slate-200 bg-panel p-4 text-sm text-muted">
        <h3 className="mb-2 text-base font-semibold text-ink">Start Here</h3>
        <p>1. Sign up and verify (if required).</p>
        <p>2. Sign in.</p>
        <p>3. Go to Search and add songs to your library.</p>
        <p>4. Go to Library and play songs.</p>
      </section>

      <ResponseViewer data={responseText} onClear={clearResponse} />
    </div>
  );
}

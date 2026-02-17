import { Navigate, Route, Routes } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import Layout from "./components/Layout";
import HomePage from "./pages/Home";
import SearchPage from "./pages/Search";
import LibraryPage from "./pages/Library";
import { api, clearSession, getSessionEmail, getToken, setSessionEmail, setToken } from "./lib/client";

export type AppHelpers = {
  api: typeof api;
  notify: (message: string) => void;
  setResponse: (data: unknown) => void;
  requireAuth: () => boolean;
  signedIn: boolean;
};

export default function App() {
  const [toast, setToast] = useState("");
  const [responseText, setResponseText] = useState("{}");
  const [signedIn, setSignedIn] = useState<boolean>(getToken().length > 0);
  const [sessionEmail, setSessionEmailState] = useState<string>(getSessionEmail());

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(""), 2200);
    return () => clearTimeout(t);
  }, [toast]);

  const signedInAs = signedIn ? `Signed in as ${sessionEmail || "current user"}` : "Signed out";

  const helpers: AppHelpers = useMemo(
    () => ({
      api,
      notify: setToast,
      setResponse: (data: unknown) => setResponseText(JSON.stringify(data, null, 2)),
      requireAuth: () => {
        if (getToken().length > 0) return true;
        setToast("Sign in first.");
        return false;
      },
      signedIn
    }),
    [signedIn]
  );

  async function signIn(email: string, password: string): Promise<void> {
    const data = (await api("/auth/signin", {
      method: "POST",
      auth: false,
      body: JSON.stringify({ email, password })
    })) as { access_token?: string };
    setToken(data.access_token || "");
    setSessionEmail(email);
    setSessionEmailState(email);
    setSignedIn(true);
    helpers.setResponse(data);
    helpers.notify("Signed in.");
  }

  async function signOut(): Promise<void> {
    try {
      await api("/auth/logout", { method: "POST", body: "{}" });
    } catch {
      // ignore server-side logout errors for local session cleanup
    }
    clearSession();
    setSessionEmailState("");
    setSignedIn(false);
    helpers.notify("Signed out.");
  }

  return (
    <Layout signedInAs={signedInAs} toast={toast}>
      <Routes>
        <Route
          path="/"
          element={
            <HomePage
              helpers={helpers}
              onSignIn={signIn}
              onSignOut={signOut}
              onSignedInEmail={setSessionEmailState}
              responseText={responseText}
              clearResponse={() => setResponseText("{}")}
            />
          }
        />
        <Route
          path="/search"
          element={<SearchPage helpers={helpers} responseText={responseText} clearResponse={() => setResponseText("{}")} />}
        />
        <Route
          path="/library"
          element={<LibraryPage helpers={helpers} responseText={responseText} clearResponse={() => setResponseText("{}")} />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

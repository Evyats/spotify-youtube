const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const TOKEN_KEY = "access_token";
const EMAIL_KEY = "session_email";

export type ApiInit = RequestInit & { auth?: boolean };

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setToken(token: string): void {
  if (!token) {
    localStorage.removeItem(TOKEN_KEY);
    return;
  }
  localStorage.setItem(TOKEN_KEY, token);
}

export function getSessionEmail(): string {
  return localStorage.getItem(EMAIL_KEY) || "";
}

export function setSessionEmail(email: string): void {
  if (!email) {
    localStorage.removeItem(EMAIL_KEY);
    return;
  }
  localStorage.setItem(EMAIL_KEY, email);
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(EMAIL_KEY);
}

export async function api(path: string, init: ApiInit = {}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined)
  };
  if (init.auth !== false) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    credentials: "include"
  });

  const text = await res.text();
  let data: unknown = text;
  try {
    data = JSON.parse(text);
  } catch {
    // keep raw text
  }

  if (!res.ok) {
    const detail =
      typeof data === "object" && data && "detail" in data ? (data as { detail?: unknown }).detail : data;
    const message = typeof detail === "string" ? detail : JSON.stringify(detail);
    throw new Error(message || `Request failed (${res.status})`);
  }

  return data;
}

export function apiBase(): string {
  return API_BASE;
}

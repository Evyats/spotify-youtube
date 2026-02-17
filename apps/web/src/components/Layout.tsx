import type { ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";

type LayoutProps = {
  children: ReactNode;
  signedInAs: string;
  toast: string;
};

export default function Layout({ children, signedInAs, toast }: LayoutProps) {
  return (
    <div className="min-h-screen bg-bg text-ink">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-panel/95 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-4 py-3">
          <div>
            <Link to="/" className="text-lg font-semibold">
              My Music
            </Link>
            <p className="text-xs text-muted">Simple personal song library</p>
          </div>
          <nav className="flex items-center gap-2">
            <NavLink to="/" className={({ isActive }) => navClass(isActive)}>
              Home
            </NavLink>
            <NavLink to="/search" className={({ isActive }) => navClass(isActive)}>
              Search
            </NavLink>
            <NavLink to="/library" className={({ isActive }) => navClass(isActive)}>
              Library
            </NavLink>
          </nav>
          <div className="rounded-md bg-accentSoft px-3 py-1 text-xs text-slate-700">{signedInAs}</div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-6">{children}</main>

      {toast ? (
        <div className="fixed bottom-4 right-4 rounded-md bg-ink px-3 py-2 text-sm text-white shadow-lg">{toast}</div>
      ) : null}
    </div>
  );
}

function navClass(isActive: boolean): string {
  return isActive
    ? "rounded-md bg-accent px-3 py-1.5 text-sm text-white"
    : "rounded-md px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100";
}

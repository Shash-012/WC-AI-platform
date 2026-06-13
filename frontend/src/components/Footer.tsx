import { Link } from "react-router-dom";

export function Footer() {
  return (
    <footer className="mt-24 border-t border-border bg-surface/40">
      <div className="mx-auto max-w-7xl px-6 py-10 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="font-display text-lg font-bold tracking-wide">
            WORLD CUP <span className="text-[var(--color-accent-text)]">2026</span>
          </p>
          <p className="text-sm text-muted mt-1">
            An AI-powered companion for the tournament. Data is illustrative.
          </p>
        </div>
        <nav className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted">
          <Link to="/groups" className="hover:text-fg transition-colors">Groups</Link>
          <Link to="/fixtures" className="hover:text-fg transition-colors">Fixtures</Link>
          <Link to="/teams" className="hover:text-fg transition-colors">Teams</Link>
          <Link to="/scout" className="hover:text-fg transition-colors">AI Scout</Link>
        </nav>
      </div>
    </footer>
  );
}

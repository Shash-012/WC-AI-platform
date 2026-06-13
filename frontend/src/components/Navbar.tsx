import { useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { Menu, X } from "@/components/icons";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/ThemeToggle";

const LINKS = [
  { to: "/", label: "Home", end: true },
  { to: "/scout", label: "AI Scout" },
  { to: "/groups", label: "Groups" },
  { to: "/fixtures", label: "Fixtures" },
  { to: "/teams", label: "Teams" },
  { to: "/predictor", label: "Predictor" },
  { to: "/sentiment", label: "Sentiment" },
];

export function Navbar() {
  const [open, setOpen] = useState(false);
  const location = useLocation();

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    cn(
      "relative text-sm font-medium transition-colors",
      isActive ? "text-fg" : "text-muted hover:text-fg"
    );

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-base/80 backdrop-blur-xl">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex h-16 items-center justify-between">
          <Link to="/" className="font-display text-xl font-extrabold tracking-wide" onClick={() => setOpen(false)}>
            WC<span className="text-[var(--color-accent-text)]">26</span>
          </Link>

          <nav className="hidden items-center gap-7 lg:flex">
            {LINKS.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.end} className={linkClass}>
                {({ isActive }) => (
                  <>
                    {l.label}
                    {isActive && (
                      <span className="absolute -bottom-[21px] left-0 right-0 h-0.5 bg-accent" />
                    )}
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-1">
            <ThemeToggle />
            <button
              className="lg:hidden inline-flex h-10 w-10 items-center justify-center rounded-full hover:bg-surface-2 transition-colors"
              onClick={() => setOpen((o) => !o)}
              aria-label="Toggle menu"
              aria-expanded={open}
            >
              {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      {open && (
        <nav className="lg:hidden border-t border-border bg-base px-6 py-4">
          <div className="flex flex-col gap-1">
            {LINKS.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.end}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  cn(
                    "rounded-xl px-4 py-3 text-sm font-medium transition-colors",
                    isActive || (l.to !== "/" && location.pathname.startsWith(l.to))
                      ? "bg-surface-2 text-fg"
                      : "text-muted hover:bg-surface-2 hover:text-fg"
                  )
                }
              >
                {l.label}
              </NavLink>
            ))}
          </div>
        </nav>
      )}
    </header>
  );
}

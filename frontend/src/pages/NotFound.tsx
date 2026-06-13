import { Link } from "react-router-dom";
import { Home } from "@/components/icons";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function NotFound() {
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-xl flex-col items-center justify-center px-6 text-center">
      <p className="font-display text-7xl font-extrabold text-[var(--color-accent-text)]">404</p>
      <h1 className="mt-2 font-display text-3xl font-bold uppercase tracking-wide">Off the pitch</h1>
      <p className="mt-3 text-muted">That page isn't part of the squad. Let's get you back.</p>
      <Link to="/" className={cn(buttonVariants({ variant: "primary" }), "mt-8")}>
        <Home className="h-4 w-4" /> Back home
      </Link>
    </div>
  );
}

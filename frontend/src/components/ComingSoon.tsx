import { Link } from "react-router-dom";
import { MessageSquare, type IconType } from "@/components/icons";
import { Aurora } from "@/components/reactbits/Aurora";
import { GradientText } from "@/components/reactbits/GradientText";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function ComingSoon({
  eyebrow,
  title,
  blurb,
  features,
  icon: Icon,
}: {
  eyebrow: string;
  title: string;
  blurb: string;
  features: string[];
  icon: IconType;
}) {
  return (
    <div className="relative mx-auto flex min-h-[70vh] max-w-3xl flex-col items-center justify-center px-6 py-20 text-center">
      <Aurora />
      <div className="relative">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-2">
          <Icon className="h-8 w-8 text-fg" />
        </div>
        <Badge tone="accent" className="mb-4">Coming soon</Badge>
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--color-accent-text)]">{eyebrow}</p>
        <h1 className="mt-3 font-display text-4xl font-extrabold uppercase tracking-wide sm:text-6xl">
          <GradientText>{title}</GradientText>
        </h1>
        <p className="mx-auto mt-4 max-w-md text-muted">{blurb}</p>

        <div className="mx-auto mt-8 flex max-w-md flex-wrap justify-center gap-2">
          {features.map((f) => (
            <span key={f} className="rounded-full border border-border bg-surface px-3 py-1.5 text-xs text-muted">
              {f}
            </span>
          ))}
        </div>

        <Link to="/scout" className={cn(buttonVariants({ variant: "primary", size: "lg" }), "mt-10")}>
          <MessageSquare className="h-5 w-5" /> Try the AI Scout instead
        </Link>
      </div>
    </div>
  );
}

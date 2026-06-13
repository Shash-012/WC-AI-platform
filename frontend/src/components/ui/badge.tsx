import { type HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: "default" | "accent" | "warn";
}

export function Badge({ className, tone = "default", ...props }: BadgeProps) {
  const tones = {
    default: "bg-surface-2 text-muted border border-border",
    accent: "bg-accent text-accent-fg",
    warn: "bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/30",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold tracking-wide",
        tones[tone],
        className
      )}
      {...props}
    />
  );
}

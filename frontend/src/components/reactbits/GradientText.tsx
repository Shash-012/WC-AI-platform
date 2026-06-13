import { type CSSProperties, type ReactNode } from "react";
import { cn } from "@/lib/utils";

/**
 * React Bits-style GradientText. Gradient runs from the foreground color into
 * the accent — kept foreground-weighted so it stays legible in both themes.
 */
export function GradientText({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  const style: CSSProperties = {
    backgroundImage:
      "linear-gradient(100deg, var(--color-fg) 0%, var(--color-fg) 45%, var(--color-accent-strong) 100%)",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    WebkitTextFillColor: "transparent",
  };
  return (
    <span className={cn("inline-block", className)} style={style}>
      {children}
    </span>
  );
}

import { type CSSProperties } from "react";
import { cn } from "@/lib/utils";

/** React Bits-style ShinyText: a sweeping highlight across the text. */
export function ShinyText({
  text,
  className,
  speed = 4,
}: {
  text: string;
  className?: string;
  speed?: number;
}) {
  const style: CSSProperties = {
    backgroundImage:
      "linear-gradient(110deg, currentColor 35%, var(--color-accent) 50%, currentColor 65%)",
    backgroundSize: "200% auto",
    WebkitBackgroundClip: "text",
    backgroundClip: "text",
    WebkitTextFillColor: "transparent",
    animation: `shine ${speed}s linear infinite`,
  };
  return (
    <span className={cn("inline-block", className)} style={style}>
      {text}
    </span>
  );
}

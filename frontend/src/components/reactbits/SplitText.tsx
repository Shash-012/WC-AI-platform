import { type CSSProperties } from "react";
import { cn } from "@/lib/utils";

/** React Bits-style SplitText: words animate up with a stagger on mount. */
export function SplitText({
  text,
  className,
  delay = 0.05,
}: {
  text: string;
  className?: string;
  delay?: number;
}) {
  const words = text.split(" ");
  return (
    <span className={cn("inline-block", className)} aria-label={text}>
      {words.map((word, i) => (
        <span key={i} className="inline-block overflow-hidden align-bottom pb-[0.08em]">
          <span
            aria-hidden
            className="inline-block will-change-transform animate-fade-up"
            style={{ animationDelay: `${i * delay}s` } as CSSProperties}
          >
            {word}
            {i < words.length - 1 ? " " : ""}
          </span>
        </span>
      ))}
    </span>
  );
}

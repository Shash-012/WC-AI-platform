import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

/** React Bits-style AnimatedList: staggered fade-up reveal of children. */
export function AnimatedList({
  children,
  className,
  stagger = 0.06,
}: {
  children: ReactNode[];
  className?: string;
  stagger?: number;
}) {
  return (
    <div className={cn(className)}>
      {children.map((child, i) => (
        <div
          key={i}
          className="animate-fade-up"
          style={{ animationDelay: `${Math.min(i, 12) * stagger}s` }}
        >
          {child}
        </div>
      ))}
    </div>
  );
}

import { type ReactNode } from "react";
import { GradientText } from "@/components/reactbits/GradientText";

export function PageHeader({
  eyebrow,
  title,
  children,
}: {
  eyebrow?: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="mx-auto max-w-3xl text-center">
      {eyebrow && (
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.25em] text-[var(--color-accent-text)]">
          {eyebrow}
        </p>
      )}
      <h1 className="font-display text-4xl font-extrabold uppercase tracking-wide sm:text-6xl">
        <GradientText>{title}</GradientText>
      </h1>
      {children && <p className="mt-4 text-base text-muted sm:text-lg">{children}</p>}
    </div>
  );
}

/** React Bits-style Aurora: soft animated color fields behind content. */
export function Aurora({ className = "" }: { className?: string }) {
  return (
    <div className={`pointer-events-none absolute inset-0 overflow-hidden ${className}`} aria-hidden>
      <div
        className="absolute -top-1/3 left-[-10%] h-[60vh] w-[60vh] rounded-full blur-3xl opacity-30"
        style={{
          background:
            "radial-gradient(circle at center, var(--color-accent) 0%, transparent 60%)",
          animation: "aurora 18s ease-in-out infinite",
        }}
      />
      <div
        className="absolute bottom-[-20%] right-[-5%] h-[55vh] w-[55vh] rounded-full blur-3xl opacity-20"
        style={{
          background:
            "radial-gradient(circle at center, #3b82f6 0%, transparent 60%)",
          animation: "aurora 22s ease-in-out infinite reverse",
        }}
      />
    </div>
  );
}

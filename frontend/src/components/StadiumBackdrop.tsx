/**
 * Self-contained cinematic "stadium at night" backdrop — pure CSS/SVG so it
 * needs no external image. Navy field with volt-tinted floodlights and a
 * perspective pitch. Used full-bleed behind the homepage hero.
 */
export function StadiumBackdrop({ className = "" }: { className?: string }) {
  return (
    <div className={`absolute inset-0 overflow-hidden bg-[#0A1628] ${className}`} aria-hidden>
      {/* deep vignette + sky glow */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(120% 80% at 50% -10%, #16335e 0%, #0d1d38 38%, #060e1e 78%)",
        }}
      />
      {/* floodlight cones */}
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 1200 800" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="flood" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#CCFF00" stopOpacity="0.32" />
            <stop offset="100%" stopColor="#CCFF00" stopOpacity="0" />
          </linearGradient>
          <radialGradient id="lamp" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#EAFFB0" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#EAFFB0" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="pitch" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0f3b1f" stopOpacity="0.0" />
            <stop offset="55%" stopColor="#15662f" stopOpacity="0.55" />
            <stop offset="100%" stopColor="#0a3d1c" stopOpacity="0.85" />
          </linearGradient>
        </defs>

        <polygon points="180,40 320,40 560,520 60,520" fill="url(#flood)" />
        <polygon points="880,40 1020,40 1140,520 640,520" fill="url(#flood)" />
        <circle cx="250" cy="48" r="60" fill="url(#lamp)" />
        <circle cx="950" cy="48" r="60" fill="url(#lamp)" />

        {/* pitch */}
        <polygon points="120,560 1080,560 1320,800 -120,800" fill="url(#pitch)" />
        <g stroke="#CCFF00" strokeOpacity="0.12" strokeWidth="2" fill="none">
          <polygon points="430,575 770,575 880,760 320,760" />
          <line x1="600" y1="575" x2="600" y2="760" />
          <ellipse cx="600" cy="668" rx="70" ry="26" />
        </g>
      </svg>

      {/* haze + grain */}
      <div
        className="absolute inset-0 mix-blend-screen opacity-40"
        style={{ background: "radial-gradient(60% 50% at 50% 30%, rgba(120,160,255,0.18), transparent 70%)" }}
      />
    </div>
  );
}

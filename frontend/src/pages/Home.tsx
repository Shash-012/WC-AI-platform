import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, MessageSquare, Trophy, Users, CalendarDays, Layers } from "@/components/icons";
import { StadiumBackdrop } from "@/components/StadiumBackdrop";
import { SplitText } from "@/components/reactbits/SplitText";
import { ShinyText } from "@/components/reactbits/ShinyText";
import { GradientText } from "@/components/reactbits/GradientText";
import { Reveal } from "@/components/Reveal";
import { Card } from "@/components/ui/card";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { teams } from "@/data/teams";
import { groups } from "@/data/groups";
import { fixtures } from "@/data/fixtures";
import { players } from "@/data/players";

const sections = [
  { to: "/scout", title: "AI Scout", desc: "Ask anything about teams, tactics, and players.", icon: MessageSquare },
  { to: "/groups", title: "Groups", desc: "All eight groups, A through H.", icon: Layers },
  { to: "/fixtures", title: "Fixtures", desc: "The opening round, June 11–17.", icon: CalendarDays },
  { to: "/teams", title: "Teams", desc: "Managers, formations, and key players.", icon: Users },
];

export function Home() {
  const [offset, setOffset] = useState(0);
  const heroRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;
    let raf = 0;
    const onScroll = () => {
      raf = requestAnimationFrame(() => setOffset(window.scrollY));
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);

  const cities = new Set(fixtures.map((f) => f.city)).size;
  const injured = players.filter((p) => p.injured).length;

  const stats = [
    { value: teams.length, label: "Teams" },
    { value: groups.length, label: "Groups" },
    { value: fixtures.length, label: "Opening fixtures" },
    { value: cities, label: "Host cities" },
  ];

  return (
    <div>
      {/* HERO */}
      <section ref={heroRef} className="relative flex h-[92vh] min-h-[560px] items-center justify-center overflow-hidden">
        <div className="absolute inset-0 will-change-transform" style={{ transform: `translateY(${offset * 0.4}px) scale(1.1)` }}>
          <StadiumBackdrop />
        </div>
        <div className="absolute inset-0" style={{ background: "var(--hero-overlay)" }} />
        <div
          className="absolute inset-x-0 bottom-0 h-40"
          style={{ background: "linear-gradient(to bottom, transparent, var(--color-base))" }}
        />

        <div className="relative z-10 mx-auto max-w-4xl px-6 text-center" style={{ transform: `translateY(${offset * 0.15}px)` }}>
          <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/5 px-4 py-1.5 text-xs font-semibold uppercase tracking-[0.2em] text-white/90 backdrop-blur">
            <Trophy className="h-3.5 w-3.5 text-[#CCFF00]" /> FIFA World Cup 2026
          </span>

          <h1 className="mt-6 font-display text-5xl font-extrabold uppercase leading-[0.95] tracking-wide text-white sm:text-7xl md:text-8xl">
            <SplitText text="The tournament," />
            <br />
            <span className="text-[#CCFF00]">
              <SplitText text="decoded by AI" delay={0.06} />
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-xl text-base text-white/80 sm:text-lg">
            <ShinyText text="Scout every squad, group, and fixture — then ask the AI anything." />
          </p>

          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link to="/scout" className={cn(buttonVariants({ variant: "primary", size: "lg" }))}>
              <MessageSquare className="h-5 w-5" /> Ask the AI Scout
            </Link>
            <Link
              to="/groups"
              className={cn(
                buttonVariants({ variant: "outline", size: "lg" }),
                "border-white/30 text-white hover:bg-white/10 hover:border-white/50"
              )}
            >
              Explore the groups <ArrowRight className="h-5 w-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* STATS */}
      <section className="mx-auto max-w-7xl px-6 -mt-10 relative z-20">
        <Card className="grid grid-cols-2 gap-px overflow-hidden bg-border/60 md:grid-cols-4">
          {stats.map((s) => (
            <div key={s.label} className="bg-surface px-6 py-8 text-center">
              <div className="font-display text-4xl font-extrabold sm:text-5xl">
                <GradientText>{String(s.value)}</GradientText>
              </div>
              <div className="mt-1 text-xs font-semibold uppercase tracking-widest text-muted">{s.label}</div>
            </div>
          ))}
        </Card>
      </section>

      {/* QUICK LINKS */}
      <section className="mx-auto max-w-7xl px-6 py-20">
        <Reveal>
          <div className="mb-10 text-center">
            <h2 className="font-display text-3xl font-bold uppercase tracking-wide sm:text-4xl">
              Everything for matchday
            </h2>
            <p className="mt-3 text-muted">Jump straight into the part of the tournament you care about.</p>
          </div>
        </Reveal>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {sections.map((s, i) => (
            <Reveal key={s.to} delay={i * 80}>
              <Link to={s.to} className="group block h-full">
                <Card className="flex h-full flex-col p-6 transition-all duration-300 hover:-translate-y-1 hover:border-accent/50 hover:shadow-[0_18px_40px_-20px_var(--color-ring)]">
                  <div className="mb-5 inline-flex h-12 w-12 items-center justify-center rounded-xl bg-surface-2 text-fg transition-colors group-hover:bg-accent group-hover:text-accent-fg">
                    <s.icon className="h-6 w-6" />
                  </div>
                  <h3 className="font-display text-xl font-bold tracking-wide">{s.title}</h3>
                  <p className="mt-2 flex-1 text-sm text-muted">{s.desc}</p>
                  <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-fg">
                    Open <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                  </span>
                </Card>
              </Link>
            </Reveal>
          ))}
        </div>
      </section>

      {/* SCOUT CTA BANNER */}
      <section className="mx-auto max-w-7xl px-6 pb-8">
        <Reveal>
          <div className="relative overflow-hidden rounded-3xl border border-border bg-surface p-10 sm:p-14">
            <div className="absolute -right-16 -top-16 h-64 w-64 rounded-full bg-accent/20 blur-3xl" />
            <div className="relative max-w-2xl">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--color-accent-text)]">AI Scout</p>
              <h2 className="mt-3 font-display text-3xl font-extrabold uppercase tracking-wide sm:text-5xl">
                Your tactical analyst, on demand
              </h2>
              <p className="mt-4 text-muted">
                {injured > 0
                  ? `Curious who is fit? ${injured} key players are carrying injury concerns. Ask the Scout for the latest read on any squad.`
                  : "Ask the Scout for a read on any squad, group, or player."}
              </p>
              <Link to="/scout" className={cn(buttonVariants({ variant: "primary", size: "lg" }), "mt-7")}>
                <MessageSquare className="h-5 w-5" /> Start a conversation
              </Link>
            </div>
          </div>
        </Reveal>
      </section>
    </div>
  );
}

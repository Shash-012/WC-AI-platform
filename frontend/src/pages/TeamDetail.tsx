import { Link, useParams } from "react-router-dom";
import { ArrowLeft, MessageSquare, MapPin, ShieldAlert, Trophy } from "@/components/icons";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { TeamBadge } from "@/components/TeamBadge";
import { GradientText } from "@/components/reactbits/GradientText";
import { Reveal } from "@/components/Reveal";
import { getTeam } from "@/data/teams";
import { groupOf, playersForTeam, fixturesForTeam, teamId } from "@/data/lookups";
import { askScoutLink, cn } from "@/lib/utils";

export function TeamDetail() {
  const { id } = useParams();
  const team = id ? getTeam(id) : undefined;

  if (!team) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-24 text-center">
        <h1 className="font-display text-3xl font-bold">Team not found</h1>
        <Link to="/teams" className={cn(buttonVariants({ variant: "outline" }), "mt-6")}>
          <ArrowLeft className="h-4 w-4" /> Back to teams
        </Link>
      </div>
    );
  }

  const grp = groupOf(team.name);
  const stars = playersForTeam(team);
  const games = fixturesForTeam(team.name);

  return (
    <div className="mx-auto max-w-5xl px-6 py-10 sm:py-14">
      <Link to="/teams" className="inline-flex items-center gap-1.5 text-sm text-muted transition-colors hover:text-fg">
        <ArrowLeft className="h-4 w-4" /> All teams
      </Link>

      {/* header */}
      <div className="mt-6 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-5">
          <TeamBadge name={team.name} className="h-20 w-20 text-2xl" />
          <div>
            <h1 className="font-display text-4xl font-extrabold uppercase tracking-wide sm:text-5xl">
              <GradientText>{team.name}</GradientText>
            </h1>
            <p className="mt-1 text-muted">Managed by {team.manager}</p>
          </div>
        </div>
        <Link to={askScoutLink(`Tell me about ${team.name}'s chances and tactics at the 2026 World Cup.`)}
          className={cn(buttonVariants({ variant: "primary" }))}>
          <MessageSquare className="h-4 w-4" /> Ask Scout about {team.name}
        </Link>
      </div>

      {/* quick facts */}
      <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Card className="p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Formation</p>
          <p className="mt-1 font-display text-2xl font-bold">{team.formation || "Flexible"}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Group</p>
          <p className="mt-1 font-display text-2xl font-bold">{grp ? `Group ${grp}` : "—"}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs font-semibold uppercase tracking-widest text-muted">Manager</p>
          <p className="mt-1 font-display text-2xl font-bold leading-tight">{team.manager}</p>
        </Card>
      </div>

      {/* description */}
      <Reveal>
        <Card className="mt-6 p-6">
          <h2 className="font-display text-lg font-bold uppercase tracking-wide">Scouting report</h2>
          <p className="mt-3 leading-relaxed text-muted">{team.description}</p>
        </Card>
      </Reveal>

      {/* key players */}
      {stars.length > 0 && (
        <div className="mt-10">
          <h2 className="mb-4 font-display text-2xl font-bold uppercase tracking-wide">Key players</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {stars.map((p, i) => (
              <Reveal key={p.slug} delay={i * 60}>
                <Card className="h-full p-5">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="font-display text-xl font-bold tracking-wide">{p.name}</h3>
                      <p className="text-sm text-muted">{p.position} · {p.club}</p>
                    </div>
                    {p.injured ? (
                      <Badge tone="warn"><ShieldAlert className="h-3 w-3" /> {p.status}</Badge>
                    ) : (
                      <Badge tone="accent"><Trophy className="h-3 w-3" /> Available</Badge>
                    )}
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-muted">{p.achievements}</p>
                </Card>
              </Reveal>
            ))}
          </div>
        </div>
      )}

      {/* fixtures */}
      {games.length > 0 && (
        <div className="mt-10">
          <h2 className="mb-4 font-display text-2xl font-bold uppercase tracking-wide">Opening fixture</h2>
          <div className="space-y-3">
            {games.map((f) => {
              const opp = f.home === team.name ? f.away : f.home;
              const oppId = teamId(opp);
              return (
                <Card key={f.id} className="flex flex-wrap items-center gap-x-4 gap-y-2 p-5">
                  <span className="font-display text-lg font-bold tracking-wide">
                    {f.home} <span className="text-muted">vs</span> {f.away}
                  </span>
                  <span className="flex items-center gap-1.5 text-xs text-muted">
                    <MapPin className="h-3.5 w-3.5" /> {f.venue}, {f.city} · {f.date}
                  </span>
                  {oppId && (
                    <Link to={`/teams/${oppId}`} className="ml-auto text-sm font-semibold text-fg hover:text-[var(--color-accent-text)]">
                      Scout {opp} →
                    </Link>
                  )}
                </Card>
              );
            })}
          </div>
        </div>
      )}

      <div className="mt-12 flex justify-center">
        <Link to={askScoutLink(`How should ${team.name} approach their opening match?`)}
          className={cn(buttonVariants({ variant: "outline", size: "lg" }))}>
          <MessageSquare className="h-5 w-5" /> Ask the Scout a tactical question
        </Link>
      </div>
    </div>
  );
}

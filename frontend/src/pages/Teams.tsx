import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Search, ArrowUpRight } from "@/components/icons";
import { PageHeader } from "@/components/PageHeader";
import { Reveal } from "@/components/Reveal";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TeamBadge } from "@/components/TeamBadge";
import { teams } from "@/data/teams";
import { groupOf, playersForTeam } from "@/data/lookups";

export function Teams() {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = !q
      ? teams
      : teams.filter(
          (t) =>
            t.name.toLowerCase().includes(q) ||
            t.manager.toLowerCase().includes(q) ||
            t.formation.includes(q)
        );
    return [...list].sort((a, b) => a.name.localeCompare(b.name));
  }, [query]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-14 sm:py-20">
      <PageHeader eyebrow="The Squads" title="Teams">
        All {teams.length} nations — managers, formations, and standout players.
      </PageHeader>

      <div className="mx-auto mt-10 flex max-w-md items-center gap-2 rounded-full border border-border bg-surface px-5 focus-within:border-accent transition-colors">
        <Search className="h-4 w-4 text-muted" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search team, manager, or formation…"
          className="h-11 flex-1 bg-transparent text-sm text-fg placeholder:text-muted focus:outline-none"
          aria-label="Search teams"
        />
      </div>

      <p className="mt-4 text-center text-xs text-muted">
        {filtered.length} {filtered.length === 1 ? "team" : "teams"}
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((t, i) => {
          const grp = groupOf(t.name);
          const stars = playersForTeam(t);
          return (
            <Reveal key={t.id} delay={Math.min(i, 8) * 40}>
              <Link to={`/teams/${t.id}`} className="group block h-full">
                <Card className="flex h-full flex-col p-5 transition-all duration-300 hover:-translate-y-1 hover:border-accent/50">
                  <div className="flex items-start gap-3">
                    <TeamBadge name={t.name} className="h-12 w-12 text-sm" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="truncate font-display text-xl font-bold tracking-wide">{t.name}</h3>
                        <ArrowUpRight className="h-4 w-4 shrink-0 text-muted transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                      </div>
                      <p className="truncate text-sm text-muted">{t.manager}</p>
                    </div>
                  </div>
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    {grp && <Badge>Group {grp}</Badge>}
                    {t.formation ? <Badge tone="accent">{t.formation}</Badge> : <Badge>Flexible</Badge>}
                    {stars.length > 0 && (
                      <span className="text-xs text-muted">
                        {stars.length} key {stars.length === 1 ? "player" : "players"}
                      </span>
                    )}
                  </div>
                </Card>
              </Link>
            </Reveal>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <p className="mt-16 text-center text-muted">No teams match “{query}”.</p>
      )}
    </div>
  );
}

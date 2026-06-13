import { Link } from "react-router-dom";
import { MapPin, MessageSquare } from "@/components/icons";
import { PageHeader } from "@/components/PageHeader";
import { Reveal } from "@/components/Reveal";
import { Card } from "@/components/ui/card";
import { TeamBadge } from "@/components/TeamBadge";
import { Badge } from "@/components/ui/badge";
import { fixtures } from "@/data/fixtures";
import { teamId, groupOf } from "@/data/lookups";
import { askScoutLink } from "@/lib/utils";

function TeamSide({ name, align }: { name: string; align: "left" | "right" }) {
  const id = teamId(name);
  const content = (
    <span className={`flex items-center gap-2.5 ${align === "right" ? "flex-row-reverse text-right" : ""}`}>
      <TeamBadge name={name} className="h-10 w-10 text-xs" />
      <span className="font-display text-lg font-bold tracking-wide">{name}</span>
    </span>
  );
  return id ? (
    <Link to={`/teams/${id}`} className="transition-opacity hover:opacity-80">{content}</Link>
  ) : (
    content
  );
}

export function Fixtures() {
  const byDate = fixtures.reduce<Record<string, typeof fixtures>>((acc, f) => {
    (acc[f.date] ||= []).push(f);
    return acc;
  }, {});

  return (
    <div className="mx-auto max-w-4xl px-6 py-14 sm:py-20">
      <PageHeader eyebrow="Matchday" title="Opening Fixtures">
        The first round of group games, June 11–17, 2026.
      </PageHeader>

      <div className="mt-14 space-y-10">
        {Object.entries(byDate).map(([date, list]) => (
          <div key={date}>
            <div className="mb-4 flex items-center gap-3">
              <h2 className="font-display text-sm font-bold uppercase tracking-[0.2em] text-muted">{date}</h2>
              <span className="h-px flex-1 bg-border" />
            </div>
            <div className="space-y-3">
              {list.map((f, i) => {
                const grp = groupOf(f.home);
                return (
                  <Reveal key={f.id} delay={i * 50}>
                    <Card className="p-5">
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex-1">
                          <TeamSide name={f.home} align="left" />
                        </div>
                        <span className="px-3 font-display text-sm font-bold text-muted">VS</span>
                        <div className="flex-1 flex justify-end">
                          <TeamSide name={f.away} align="right" />
                        </div>
                      </div>
                      <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-border pt-3 text-xs text-muted">
                        <span className="flex items-center gap-1.5">
                          <MapPin className="h-3.5 w-3.5" /> {f.venue}, {f.city}
                        </span>
                        {grp && <Badge>Group {grp}</Badge>}
                        <Link
                          to={askScoutLink(`Who has the edge in ${f.home} vs ${f.away}, and why?`)}
                          className="ml-auto inline-flex items-center gap-1.5 font-semibold text-fg transition-colors hover:text-[var(--color-accent-text)]"
                        >
                          <MessageSquare className="h-3.5 w-3.5" /> Ask Scout about this
                        </Link>
                      </div>
                    </Card>
                  </Reveal>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

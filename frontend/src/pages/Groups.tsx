import { Link } from "react-router-dom";
import { ArrowRight, MessageSquare } from "@/components/icons";
import { PageHeader } from "@/components/PageHeader";
import { Reveal } from "@/components/Reveal";
import { Card } from "@/components/ui/card";
import { TeamBadge } from "@/components/TeamBadge";
import { groups } from "@/data/groups";
import { teamId } from "@/data/lookups";
import { askScoutLink } from "@/lib/utils";

export function Groups() {
  return (
    <div className="mx-auto max-w-7xl px-6 py-14 sm:py-20">
      <PageHeader eyebrow="Group Stage" title="The Eight Groups">
        Groups A through H. Four teams in each — tap any side for the full breakdown.
      </PageHeader>

      <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {groups.map((g, i) => (
          <Reveal key={g.letter} delay={(i % 4) * 70}>
            <Card className="flex h-full flex-col p-5">
              <div className="mb-4 flex items-center justify-between">
                <span className="font-display text-3xl font-extrabold tracking-wide">
                  Group {g.letter}
                </span>
                <Link
                  to={askScoutLink(`Give me a preview of Group ${g.letter} at the 2026 World Cup.`)}
                  className="text-muted transition-colors hover:text-fg"
                  title="Ask Scout about this group"
                  aria-label={`Ask Scout about Group ${g.letter}`}
                >
                  <MessageSquare className="h-4 w-4" />
                </Link>
              </div>

              <ul className="flex flex-1 flex-col gap-1.5">
                {g.teams.map((name) => {
                  const id = teamId(name);
                  const inner = (
                    <span className="flex items-center gap-3 rounded-xl px-2 py-2 transition-colors hover:bg-surface-2">
                      <TeamBadge name={name} className="h-9 w-9 text-xs" />
                      <span className="text-sm font-medium">{name}</span>
                      {id && <ArrowRight className="ml-auto h-4 w-4 text-muted" />}
                    </span>
                  );
                  return (
                    <li key={name}>
                      {id ? <Link to={`/teams/${id}`}>{inner}</Link> : inner}
                    </li>
                  );
                })}
              </ul>
            </Card>
          </Reveal>
        ))}
      </div>
    </div>
  );
}

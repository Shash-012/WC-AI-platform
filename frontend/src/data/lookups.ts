// Hand-written helpers over the auto-generated data (kept separate so a
// regenerate never clobbers them).
import { teams } from "./teams";
import { players } from "./players";
import { groups } from "./groups";
import { fixtures } from "./fixtures";
import type { Player, Team } from "./types";

const idByName = new Map(teams.map((t) => [t.name, t.id] as const));

export function teamId(name: string): string | undefined {
  return idByName.get(name);
}

const groupByTeam = new Map<string, string>();
for (const g of groups) for (const t of g.teams) groupByTeam.set(t, g.letter);

export function groupOf(teamName: string): string | undefined {
  return groupByTeam.get(teamName);
}

export function playersForTeam(team: Team): Player[] {
  return team.keyPlayers
    .map((n) => players.find((p) => p.name === n))
    .filter((p): p is Player => Boolean(p));
}

export function fixturesForTeam(teamName: string) {
  return fixtures.filter((f) => f.home === teamName || f.away === teamName);
}

export const injuredPlayers = players.filter((p) => p.injured);

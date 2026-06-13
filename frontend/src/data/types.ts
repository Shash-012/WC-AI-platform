// AUTO-GENERATED from backend/data seed files. Do not edit by hand.

export interface Player { name: string; country: string; club: string; position: string; achievements: string; status: string; injured: boolean; slug: string; }
export interface Team { id: string; name: string; manager: string; formation: string; description: string; keyPlayers: string[]; }
export interface Group { letter: string; teams: string[]; description: string; }
export interface Fixture { id: number; home: string; away: string; homeRaw: string; awayRaw: string; date: string; venue: string; city: string; }

export interface PlayerListItem {
  id: number;
  nhl_id: number;
  name: string;
  team: string;
  position: string;
  position_category: 'Center' | 'Wing' | 'Defenseman';
  ranking: number;
  previous_ranking: number | null;
  iq_score: number;
  consecutive_weeks: number;
  games: number;
  goals: number;
  assists: number;
  points: number;
  plus_minus: number;
  headshot_url: string;
}

export interface PlayerDetail extends PlayerListItem {
  number: number;
  primary_assists: number;
  time_on_ice_per_game: number;
  points_per_60: number;
  primary_assists_per_60: number;
  plus_minus_per_60: number;
  corsi_percentage: number;
  xgoals_percentage: number;
  description: string;
  updated_at: string;
  videos: { youtube_url: string; title: string; display_order: number }[];
  weekly_appearances: {
    week_number: number;
    ranking: number;
    previous_ranking: number | null;
    goals: number;
    assists: number;
    points: number;
    plus_minus: number;
  }[];
}

export type PositionFilter = 'All' | 'Center' | 'Wing' | 'Defenseman';

export async function fetchPlayers(position?: PositionFilter): Promise<PlayerListItem[]> {
  const params = new URLSearchParams();
  if (position && position !== 'All') params.set('position', position);
  const query = params.toString();
  const res = await fetch(`/api/players${query ? `?${query}` : ''}`);
  if (!res.ok) throw new Error(`Failed to fetch players: ${res.status}`);
  return res.json();
}

export async function fetchPlayer(nhlId: number): Promise<PlayerDetail> {
  const res = await fetch(`/api/players/${nhlId}`);
  if (!res.ok) throw new Error(`Failed to fetch player ${nhlId}: ${res.status}`);
  return res.json();
}

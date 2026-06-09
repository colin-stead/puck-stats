import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { fetchPlayers, type PlayerListItem, type PositionFilter } from '@/api';

interface PlayerTableProps {
  positionFilter: PositionFilter;
}

export function PlayerTable({ positionFilter }: PlayerTableProps) {
  const navigate = useNavigate();
  const [players, setPlayers] = useState<PlayerListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchPlayers(positionFilter)
      .then(setPlayers)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [positionFilter]);

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-lg">Loading skaters...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="text-lg text-red-600">Failed to load players: {error}</div>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr className="border-b-2 border-gray-300">
            <th className="p-4 text-left">Rank</th>
            <th className="p-4 text-left">Skater</th>
            <th className="p-4 text-left">Team</th>
            <th className="p-4 text-center">Pos</th>
            <th className="p-4 text-center">Streak</th>
            <th className="p-4 text-center">GP</th>
            <th className="p-4 text-center">G</th>
            <th className="p-4 text-center">A</th>
            <th className="p-4 text-center">P</th>
            <th className="p-4 text-center">+/-</th>
            <th className="p-4 text-center">IQ</th>
          </tr>
        </thead>
        <tbody>
          {players.map((player) => {
            const rankDelta = player.previous_ranking != null ? player.previous_ranking - player.ranking : null;
            return (
              <tr
                key={player.id}
                onClick={() => navigate(`/player/${player.nhl_id}`)}
                className="border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition-colors"
              >
                <td className="p-4">
                  <div className="flex items-center gap-1">
                    <span className="font-bold text-lg">{player.ranking}</span>
                    {rankDelta !== null && (
                      <span className={`text-xs font-semibold ${rankDelta > 0 ? 'text-green-600' : rankDelta < 0 ? 'text-red-600' : 'text-gray-400'}`}>
                        {rankDelta > 0 ? `▲${rankDelta}` : rankDelta < 0 ? `▼${Math.abs(rankDelta)}` : '—'}
                      </span>
                    )}
                  </div>
                </td>
                <td className="p-4">
                  <div className="flex items-center gap-3">
                    <img
                      src={player.headshot_url || `https://cms.nhl.bamgrid.com/images/headshots/current/168x168/${player.nhl_id}.jpg`}
                      alt={player.name}
                      className="w-12 h-12 rounded-full object-cover"
                      onError={(e) => {
                        e.currentTarget.src = 'https://via.placeholder.com/168x168?text=NHL';
                      }}
                    />
                    <span className="font-semibold">{player.name}</span>
                  </div>
                </td>
                <td className="p-4">{player.team}</td>
                <td className="p-4 text-center">{player.position}</td>
                <td className="p-4 text-center">
                  <span className="text-sm text-gray-500" title="Consecutive weeks in top 10">
                    {player.consecutive_weeks > 0 ? `${player.consecutive_weeks}w` : '—'}
                  </span>
                </td>
                <td className="p-4 text-center">{player.games}</td>
                <td className="p-4 text-center font-semibold">{player.goals}</td>
                <td className="p-4 text-center font-semibold">{player.assists}</td>
                <td className="p-4 text-center font-bold text-blue-600">{player.points}</td>
                <td className={`p-4 text-center font-semibold ${player.plus_minus >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {player.plus_minus > 0 ? '+' : ''}{player.plus_minus}
                </td>
                <td className="p-4 text-center font-semibold text-purple-600">{player.iq_score}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export type { PlayerListItem as Player };

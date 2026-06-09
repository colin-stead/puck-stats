import { useParams, useNavigate } from 'react-router';
import { ArrowLeft, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useEffect, useState } from 'react';
import { fetchPlayer, type PlayerDetail as PlayerDetailType } from '@/api';

export function PlayerDetail() {
  const { playerId } = useParams();
  const navigate = useNavigate();
  const [player, setPlayer] = useState<PlayerDetailType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!playerId) return;
    setLoading(true);
    fetchPlayer(Number(playerId))
      .then(setPlayer)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [playerId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading skater...</div>
      </div>
    );
  }

  if (error || !player) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-4">Skater Not Found</h2>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Back to Rankings
          </button>
        </div>
      </div>
    );
  }

  const rankDelta = player.previous_ranking != null ? player.previous_ranking - player.ranking : null;
  const toiFormatted = (() => {
    const totalSecs = Math.round(player.time_on_ice_per_game * 60);
    const m = Math.floor(totalSecs / 60);
    const s = String(totalSecs % 60).padStart(2, '0');
    return `${m}:${s}`;
  })();

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-6 py-8">
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-blue-600 hover:text-blue-800 mb-6 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Rankings
        </button>

        {/* Header card */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <div className="flex flex-col md:flex-row gap-8 items-start">
            <img
              src={player.headshot_url || `https://cms.nhl.bamgrid.com/images/headshots/current/168x168/${player.nhl_id}.jpg`}
              alt={player.name}
              className="w-48 h-48 rounded-lg object-cover shadow-md"
              onError={(e) => { e.currentTarget.src = 'https://via.placeholder.com/168x168?text=NHL'; }}
            />
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <span className="text-5xl font-bold text-gray-300">#{player.ranking}</span>
                <h1 className="text-4xl font-bold">{player.name}</h1>
                {rankDelta !== null && rankDelta !== 0 && (
                  <span className={`flex items-center gap-1 text-sm font-semibold px-2 py-1 rounded-full ${rankDelta > 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {rankDelta > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                    {Math.abs(rankDelta)}
                  </span>
                )}
                {rankDelta === 0 && (
                  <span className="flex items-center gap-1 text-sm font-semibold px-2 py-1 rounded-full bg-gray-100 text-gray-500">
                    <Minus className="w-4 h-4" /> Same
                  </span>
                )}
              </div>
              <p className="text-xl text-gray-600 mb-1">{player.team} · {player.position}</p>
              {player.consecutive_weeks > 0 && (
                <p className="text-sm text-blue-600 font-medium mb-4">
                  {player.consecutive_weeks} consecutive week{player.consecutive_weeks !== 1 ? 's' : ''} in top 10
                </p>
              )}

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
                <StatCard label="Points" value={player.points} color="blue" />
                <StatCard label="Goals" value={player.goals} color="green" />
                <StatCard label="Assists" value={player.assists} color="purple" />
                <StatCard label="+/-" value={player.plus_minus > 0 ? `+${player.plus_minus}` : player.plus_minus} color={player.plus_minus >= 0 ? 'green' : 'red'} />
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Season stats */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6">Season Statistics</h2>
            <div className="space-y-1">
              <StatRow label="Games Played" value={player.games} />
              <StatRow label="Shots on Goal" value={player.shots_on_goal} />
              <StatRow label="Shooting %" value={`${player.shooting_percentage}%`} />
              <StatRow label="Time on Ice / Game" value={toiFormatted} />
              <StatRow label="Power Play Goals" value={player.power_play_goals} />
              <StatRow label="Power Play Points" value={player.power_play_points} />
              <StatRow label="Short Handed Goals" value={player.short_handed_goals} />
              <StatRow label="Game Winning Goals" value={player.game_winning_goals} />
            </div>
          </div>

          {/* AI scouting report */}
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-2">Skater Analysis</h2>
            {player.latest_description ? (
              <>
                <p className="text-xs text-gray-400 mb-4">
                  IQ {player.latest_description.iq_score_at_time} · {player.latest_description.consecutive_weeks_at_time}w streak · updated {new Date(player.latest_description.created_at).toLocaleDateString()}
                </p>
                <p className="text-gray-700 leading-relaxed">{player.latest_description.description}</p>
              </>
            ) : (
              <p className="text-gray-400 italic">Analysis will be available after the first weekly refresh.</p>
            )}
          </div>
        </div>

        {/* Advanced stats */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold mb-6">Advanced Stats</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <AdvancedStatCard label="TopShelfIQ Score" value={player.iq_score} subtitle="composite" />
            <AdvancedStatCard label="Corsi %" value={`${player.corsi_percentage}%`} subtitle="possession" />
            <AdvancedStatCard label="xGoals %" value={`${player.xgoals_percentage}%`} subtitle="shot quality" />
            <AdvancedStatCard label="Points / 60" value={player.points_per_60} subtitle="per 60 min" />
            <AdvancedStatCard label="Prim. Assists / 60" value={player.primary_assists_per_60} subtitle="per 60 min" />
            <AdvancedStatCard label="+/- per 60" value={player.plus_minus_per_60} subtitle="per 60 min" />
            <AdvancedStatCard label="Zone Entries %" value={`${player.zone_entry_success}%`} subtitle="controlled" />
            <AdvancedStatCard label="DZ Exits / 60" value={player.defensive_zone_exits} subtitle="clean exits" />
          </div>
        </div>

        {/* Weekly history */}
        {player.weekly_appearances.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <h2 className="text-2xl font-bold mb-6">Weekly History</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="py-2 px-3 text-left">Week</th>
                    <th className="py-2 px-3 text-left">Season</th>
                    <th className="py-2 px-3 text-center">Rank</th>
                    <th className="py-2 px-3 text-center">Points</th>
                    <th className="py-2 px-3 text-center">IQ Score</th>
                  </tr>
                </thead>
                <tbody>
                  {player.weekly_appearances.map((w) => (
                    <tr key={`${w.season}-${w.week_number}`} className="border-b border-gray-100">
                      <td className="py-2 px-3">{w.week_number}</td>
                      <td className="py-2 px-3">{w.season}</td>
                      <td className="py-2 px-3 text-center font-semibold">#{w.ranking}</td>
                      <td className="py-2 px-3 text-center">{w.points}</td>
                      <td className="py-2 px-3 text-center text-purple-600 font-semibold">{w.iq_score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Videos */}
        {player.videos.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-6">Skater Highlights & Analysis</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {player.videos.map((video, index) => (
                <div key={index} className="flex flex-col gap-2">
                  {video.title && <h3 className="font-semibold text-gray-700">{video.title}</h3>}
                  <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
                    <iframe
                      className="absolute top-0 left-0 w-full h-full rounded-lg"
                      src={video.youtube_url}
                      title={video.title || `${player.name} Video ${index + 1}`}
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    red: 'bg-red-50 text-red-600',
  };
  return (
    <div className={`${colorMap[color] ?? colorMap.blue} rounded-lg p-4`}>
      <p className="text-sm text-gray-600">{label}</p>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-gray-100">
      <span className="text-gray-600">{label}</span>
      <span className="font-semibold text-lg">{value}</span>
    </div>
  );
}

function AdvancedStatCard({ label, value, subtitle }: { label: string; value: string | number; subtitle: string }) {
  return (
    <div className="bg-gray-50 rounded-lg p-4 text-center">
      <p className="text-xs text-gray-500 mb-1">{subtitle}</p>
      <p className="text-2xl font-bold text-gray-800">{value}</p>
      <p className="text-sm text-gray-600 mt-1">{label}</p>
    </div>
  );
}

import { useState, useEffect } from 'react';
import { PlayerTable } from './PlayerTable';
import { VideoSection } from './VideoSection';
import { AlgorithmDescription } from './AlgorithmDescription';
import { PositionFilter } from './PositionFilter';
import { fetchPlayers, type PositionFilter as PositionFilterType } from '@/api';

export function HomePage() {
  const [positionFilter, setPositionFilter] = useState<PositionFilterType>('All');
  const [topVideoPlayers, setTopVideoPlayers] = useState<{ name: string; youtubeUrl?: string }[]>([]);

  useEffect(() => {
    fetchPlayers('All')
      .then((players) =>
        setTopVideoPlayers(
          players.slice(0, 3).map((p) => ({ name: p.name }))
        )
      )
      .catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Top 10 NHL Skaters
          </h1>
          <p className="text-xl text-gray-600">
            The definitive ranking of hockey's elite performers
          </p>
        </header>

        <AlgorithmDescription />

        <div className="bg-white rounded-xl shadow-xl p-8 mb-8">
          <h2 className="text-3xl font-bold mb-6">2025-26 Rankings</h2>
          <PositionFilter
            selectedPosition={positionFilter}
            onPositionChange={setPositionFilter}
          />
          <PlayerTable positionFilter={positionFilter} />
        </div>

        <VideoSection players={topVideoPlayers} />
      </div>
    </div>
  );
}

interface VideoSectionProps {
  players: Array<{
    name: string;
    youtubeUrl?: string;
  }>;
}

export function VideoSection({ players }: VideoSectionProps) {
  const topThreePlayers = players.slice(0, 3).filter(p => p.youtubeUrl);

  if (topThreePlayers.length === 0) {
    return null;
  }

  return (
    <div className="mt-12 mb-8">
      <h2 className="text-3xl font-bold mb-6">Watch The Best In Action</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {topThreePlayers.map((player, index) => (
          <div key={index} className="flex flex-col">
            <h3 className="text-xl font-semibold mb-3">{player.name} - Player Analysis</h3>
            <div className="relative w-full" style={{ paddingBottom: '56.25%' }}>
              <iframe
                className="absolute top-0 left-0 w-full h-full rounded-lg shadow-lg"
                src={player.youtubeUrl}
                title={`${player.name} Analysis`}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

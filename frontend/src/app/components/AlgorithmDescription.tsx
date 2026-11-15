export function AlgorithmDescription() {
  return (
    <div className="my-12 p-8 bg-gradient-to-br from-blue-50 to-gray-50 rounded-lg border border-gray-200">
      <h2 className="text-3xl font-bold mb-4">Our Ranking Algorithm</h2>
      <div className="text-gray-700 leading-relaxed space-y-4">
        <p>
          The Hockey IQ score is built from 8 factors that are each multiplied by a weight and added together.
          To be eligible, a skater must average at least 10 minutes of ice time per game and, once anyone has
          played 10 games, must have played at least 10 games themselves.
        </p>
        <p>
          Points, primary assists, and plus/minus are converted to a "per 60 minutes" rate so that players who log less
          ice time aren't unfairly penalized. Deeper analytical stats like Corsi% (how often your team controls shot
          attempts when a player is on the ice) and Expected Goals% (the quality of scoring chances the player's team
          generates with them on the ice) are already percentages, so they go straight in.
        </p>
        <p>
          Elite workload earns a bonus: forwards averaging 21+ minutes a game and defensemen averaging 23+ get a flat
          2.0 points, plus 0.10 for every additional minute above that threshold.
        </p>
        <p>
          Finally we deduct for penalty minutes per 60 (to ensure we're not rewarding goons — penalties are prime examples
          of dumb hockey) and for Expected Goals Against per 60, rewarding defensively solid players. A smart player
          should be effective in all settings.
        </p>
        <ul className="list-disc pl-6 space-y-1">
          <li>Points per 60: +20%</li>
          <li>Corsi%: +20%</li>
          <li>Primary assists per 60: +15%</li>
          <li>Expected Goals%: +15%</li>
          <li>Plus/minus per 60: +10%</li>
          <li>Elite ice-time bonus: 2.0 + 0.10 per minute above the threshold</li>
          <li>Penalty minutes per 60: −15%</li>
          <li>Expected Goals Against per 60: −10%</li>
        </ul>
        <p>
          Add all eight together and you get the final IQ score, which reflects a mix of offensive production,
          playmaking, scoring chance quality, and two-way play in a single number. The top 10 centers, wings, and
          defensemen are ranked 1–30 overall, and each is also ranked 1–10 within their position.
        </p>
      </div>
    </div>
  );
}

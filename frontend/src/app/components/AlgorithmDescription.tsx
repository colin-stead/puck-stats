export function AlgorithmDescription() {
  return (
    <div className="my-12 p-8 bg-gradient-to-br from-blue-50 to-gray-50 rounded-lg border border-gray-200">
      <h2 className="text-3xl font-bold mb-4">Our Ranking Algorithm</h2>
      <div className="text-gray-700 leading-relaxed space-y-4">
        <p>
          The Hockey IQ score is built from 9 stats that each get multiplied by a weight before being added together.
          First, it takes in stats like points, primary assists, and plus/minus. While there is a minimum number of games played rule,
          these statistics are converted to a "per 60 minutes" rate so that players who log less ice time aren't unfairly penalized.
        </p>
        <p>
          Then, deeper analytical stats like Corsi% (how often your team controls shot attempts when a player is on the ice)
          and Expected Goals% (the quality of scoring chances the player's team generates with them on the ice)
          are already in percentage form, so they go straight in.
        </p>
        <p>
          Finally we deduct stats like penalty minutes (via PIM/60) and Expected Goals Against % to ensure we're not getting goons
          (penalties are prime examples of dumb hockey) and getting defensively solid players - another feature for smart players,
          should be effective in all settings.
        </p>
        <p>
          Once everything is scaled, each stat gets multiplied by how important it's considered to be —
          points per 60 and Corsi% carry the most influence at 20% each, primary assists and xGoals% come in at 15% each,
          and the remaining three (plus/minus per 60, defensive zone exits, and zone entry success rate) each chip in 10%.
          PIM/60 negatively influence the score by 15% and xGoals Against% negatively influences the score by 10%.
        </p>
        <p>
          Add all seven weighted numbers together and you get the final IQ score, which reflects a mix of offensive production,
          playmaking, scoring chance quality, and two-way play in a single number.
        </p>
      </div>
    </div>
  );
}

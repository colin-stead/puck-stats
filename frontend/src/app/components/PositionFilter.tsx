interface PositionFilterProps {
  selectedPosition: 'All' | 'Center' | 'Defenseman' | 'Wing';
  onPositionChange: (position: 'All' | 'Center' | 'Defenseman' | 'Wing') => void;
}

export function PositionFilter({ selectedPosition, onPositionChange }: PositionFilterProps) {
  const positions: Array<'All' | 'Center' | 'Defenseman' | 'Wing'> = ['All', 'Center', 'Wing', 'Defenseman'];

  return (
    <div className="flex flex-wrap gap-3 mb-6">
      {positions.map((position) => (
        <button
          key={position}
          onClick={() => onPositionChange(position)}
          className={`px-6 py-3 rounded-lg font-semibold transition-all ${
            selectedPosition === position
              ? 'bg-blue-600 text-white shadow-lg scale-105'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {position === 'All' ? 'All Skaters' : (position === 'Defenseman' ? 'Defensemen' : `${position}s`)}
        </button>
      ))}
    </div>
  );
}

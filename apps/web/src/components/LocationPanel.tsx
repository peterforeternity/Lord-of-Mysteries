import type { Location } from "../types";

interface Props {
  currentLocation: Location;
  locations: Location[];
  onLocationClick?: (locationId: string) => void;
}

export default function LocationPanel({
  currentLocation,
  locations,
}: Props) {
  const visitedLocations = locations.filter((l) => l.is_visited);

  return (
    <div className="card card-accent mb-4">
      <h3 className="text-mystic-gold text-sm font-bold mb-3 tracking-wider">
        当前位置
      </h3>
      <div className="mb-3">
        <p className="text-mystic-text font-medium">
          {currentLocation.name}
        </p>
        <p className="text-mystic-text-dim text-xs mt-1">
          {currentLocation.description}
        </p>
      </div>
      <div className="divider" />
      <h4 className="text-mystic-text-dim text-xs font-bold mb-2 tracking-wider">
        已探索区域
      </h4>
      {visitedLocations.length === 0 ? (
        <p className="text-mystic-text-dim text-xs italic">尚未探索其他区域</p>
      ) : (
        <ul className="space-y-1">
          {visitedLocations.map((loc) => (
            <li
              key={loc.id}
              className={`text-xs px-2 py-1 rounded ${
                loc.is_current
                  ? "bg-mystic-accent/20 text-mystic-gold"
                  : "text-mystic-text-dim"
              }`}
            >
              {loc.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

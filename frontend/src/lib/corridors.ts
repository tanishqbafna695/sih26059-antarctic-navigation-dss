// Corridor data loader and types
import corridorsIndex from "../data/corridors/index.json";

export interface Station {
  name: string;
  lat: number;
  lon: number;
}

export interface CorridorMeta {
  id: string;
  name: string;
  from: Station;
  to: Station;
  distance_km: number;
  bbox: [[number, number], [number, number]];
}

export interface RouteRow {
  route: string;
  travel_time_h: number;
  fuel_liters: number;
  mean_hazard: number;
  max_hazard: number;
  ice_exposure_frac: number;
  mean_iceberg_hazard: number;
}

export interface Confidence {
  overall_confidence: number;
  status_label: string;
}

export interface CorridorTradeoff {
  comparison: {
    routes_available: boolean;
    reason?: string;
    rows: RouteRow[];
    confidence: Confidence;
  };
  recommendations: Record<string, { recommended: string }>;
}

export interface CorridorExplanation {
  explained: boolean;
  headline?: string;
  strengths?: string[];
  prices?: string[];
  vessel_statement?: string;
  confidence_note?: string;
  caveats?: string[];
  reason?: string;
}

export interface CorridorStatus {
  depart_date: string;
  confidence: Confidence;
  ocean_source: string;
  sources: string[];
  honesty: string;
}

export const CORRIDORS: CorridorMeta[] = corridorsIndex as CorridorMeta[];

export const CORRIDOR_MAP = Object.fromEntries(
  CORRIDORS.map((c) => [c.id, c])
) as Record<string, CorridorMeta>;

// All known Antarctic stations for the origin/destination picker
export const ALL_STATIONS: Station[] = [
  // Indian
  { name: "Bharati", lat: -69.41, lon: 76.19 },
  { name: "Maitri", lat: -70.77, lon: 11.73 },
  // US
  { name: "McMurdo", lat: -77.85, lon: 166.67 },
  { name: "Palmer", lat: -64.77, lon: -64.05 },
  // UK
  { name: "Halley VI", lat: -75.58, lon: -26.65 },
  { name: "Rothera", lat: -67.57, lon: -68.13 },
  // Germany
  { name: "Neumayer III", lat: -70.65, lon: -8.27 },
  // Japan
  { name: "Syowa", lat: -69.00, lon: 39.58 },
  // Australia
  { name: "Mawson", lat: -67.60, lon: 62.88 },
  { name: "Davis", lat: -68.58, lon: 77.97 },
  { name: "Casey", lat: -66.28, lon: 110.52 },
  // Russia
  { name: "Mirny", lat: -66.55, lon: 93.02 },
  { name: "Vostok", lat: -78.47, lon: 106.83 },
  // China
  { name: "Zhongshan", lat: -69.37, lon: 76.37 },
  { name: "Great Wall", lat: -62.22, lon: -58.93 },
  // France
  { name: "Concordia", lat: -75.10, lon: 123.35 },
  // Italy
  { name: "Mario Zucchelli", lat: -74.69, lon: 164.10 },
  // South Korea
  { name: "Jang Bogo", lat: -74.62, lon: 164.22 },
  // Argentina
  { name: "Marambio", lat: -64.23, lon: -56.62 },
  // New Zealand
  { name: "Scott Base", lat: -77.85, lon: 166.76 },
  // Norway
  { name: "Troll", lat: -72.01, lon: 2.53 },
  // Brazil
  { name: "Comandante Ferraz", lat: -62.08, lon: -58.37 },
  // Poland
  { name: "Arctowski", lat: -62.15, lon: -58.41 },
  // Chile
  { name: "Villa Las Estrellas", lat: -62.20, lon: -58.96 },
];

export function findStation(name: string): Station | undefined {
  return ALL_STATIONS.find((s) => s.name === name);
}

export function haversine_km(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

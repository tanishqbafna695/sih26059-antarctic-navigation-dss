export interface RouteMetrics {
  time_h: number;
  fuel_l: number;
  risk: number;
  ice_exp: number;
  berg: number;
}

export type MetricKey = "risk" | "time_h" | "fuel_l" | "ice_exp" | "berg";

export interface ComparisonRow extends RouteMetrics {
  route: string;
}

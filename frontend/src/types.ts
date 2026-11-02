export interface Site {
  id: number;
  name: string;
  lat: number;
  lng: number;
  categories: string[];
  visit_minutes: number;
  summary?: string;
  hidden_tier?: boolean;
  confidence?: string;
  hours_verified?: boolean;
}

export interface PlanStop {
  site_id: number;
  lat: number;
  lng: number;
  walking_minutes: number;
  visit_minutes: number;
  reason: string;
  reason_codes?: string[];
}

export interface Plan {
  stops: PlanStop[];
  total_duration_minutes: number;
  finish_time: string;
  walking_minutes: number;
  visiting_minutes: number;
  reasons: Array<Record<string, unknown>>;
  route_geometry?: Array<{lat: number; lng: number}> | null;
  engine_notes?: string;
}

export type SignalType =
  | "product_launch"
  | "pricing_change"
  | "hiring_surge"
  | "partnership"
  | "exec_move"
  | "reorg"
  | "funding"
  | "revenue_proxy"
  | "growth_indicator"
  | "red_flag"
  | "market_expansion"
  | "talent_velocity"
  | "github_activity"
  | "other";

export type Urgency = "low" | "medium" | "high" | "critical";
export type Mode = "employee" | "investor" | "both";
export type Trajectory = "accelerating" | "stable" | "declining";
export type ThreatLevel = "low" | "medium" | "high" | "critical";

export interface Signal {
  id: string;
  competitor: string;
  type: SignalType;
  summary: string;
  urgency: Urgency;
  surface_now: boolean;
  detected_at: string; // ISO 8601
  source_url?: string | null;
  mode: Mode;
  image_url?: string | null;
  gemini_analysis?: string | null;
  evidence?: string;
  momentum_delta?: number;
}

export interface CompetitorSummary {
  name: string;
  trajectory: Trajectory;
  momentum_score: number;
  threat_level: ThreatLevel;
  narrative: string;
  strategic_inference: string;
  top_signals: Signal[];
  signal_count_24h: number;
}

export interface DailyReport {
  company: string;
  date: string;
  generated_at: string;
  competitors: CompetitorSummary[];
  total_signals_24h: number;
}

export interface DiscoverResponse {
  company: string;
  competitors: string[];
  cached: boolean;
}

export interface SignalsResponse {
  company: string;
  count: number;
  signals: Signal[];
}

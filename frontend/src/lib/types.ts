export interface Signal {
  id: string;
  competitor: string;
  type: "product" | "pricing" | "hiring" | "partnership" | "funding" | "other";
  summary: string;
  urgency: "low" | "medium" | "high";
  surfaceNow: boolean;
  detectedAt: string; // ISO 8601
  sourceUrl?: string;
}

export interface DailyReport {
  company: string;
  date: string; // ISO 8601
  competitors: CompetitorSummary[];
}

export interface CompetitorSummary {
  name: string;
  trajectory: string;
  topSignals: Signal[];
}

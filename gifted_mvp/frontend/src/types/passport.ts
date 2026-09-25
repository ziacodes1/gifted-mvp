import type { Confidence, SignalCategory } from "./assessment";
import type { EmergingStrength } from "./ai";
import type { MissionSummary } from "./mission";

export type PassportStatus = "EMPTY" | "EMERGING" | "GROWING";

export interface PassportSignal {
  key: string;
  label: string;
  category: SignalCategory;
  score: number;
  confidence: Confidence;
  evidence_count: number;
  opportunity_count: number;
}

export interface JourneyStage {
  key: string;
  label: string;
  done: boolean;
}

export interface PassportNextStep {
  title: string;
  activity_type: string;
  reason: string;
  intended_validation: string;
  confidence_note: string;
  signals_used: { key: string; label: string }[];
}

export interface EvidenceSummary {
  total: number;
  assessment: number;
  missions: number;
  opportunities: number;
  experiences: number;
}

export interface EvidenceItem {
  id: number;
  title: string;
  source_type: string;
  source_label: string;
  created_at: string;
  dimensions: { key: string; label: string; kind_label: string }[];
}

export interface ExploredDimension {
  key: string;
  label: string;
  kinds: string[];
  activities: number;
}

export interface Passport {
  learner: { display_name: string; first_name: string; member_since: string };
  passport_number: string;
  version: number;
  status: PassportStatus;
  journey: JourneyStage[];
  headline: string | null;
  summary: string | null;
  insight_source: "AI" | "FALLBACK" | null;
  signals: PassportSignal[];
  /** Aptitude, work style, values and exposure (incl. zero-evidence exposure = not tried yet). */
  other_signals: PassportSignal[];
  emerging_strengths: EmergingStrength[];
  exploration_gaps: string[];
  uncertainty_notes: string[];
  suggested_explorations: string[];
  insight_covers_new_evidence: boolean;
  next_step: PassportNextStep | null;
  recommended_mission: MissionSummary | null;
  evidence_summary: EvidenceSummary;
  evidence_sources: { assessments: number; missions: number };
  recent_evidence: EvidenceItem[];
  explored_dimensions: ExploredDimension[];
  message: string;
  updated_at: string;
}

import type { Confidence } from "./assessment";
import type { EmergingStrength } from "./ai";
import type { AttemptStatus } from "./mission";
import type { EvidenceSummary, ExploredDimension, JourneyStage, PassportSignal, PassportStatus } from "./passport";

export interface ParentChildSummary {
  id: number;
  display_name: string;
}

export interface ParentInsightContent {
  summary: string;
  what_we_are_seeing: { title: string; explanation: string }[];
  what_is_still_unclear: string[];
  support_at_home: { title: string; action: string }[];
  conversation_starter: string;
  caution: string;
}

export interface ParentInsight {
  source: "AI" | "FALLBACK";
  content: ParentInsightContent;
  generated_at: string;
}

export interface ParentOverview {
  learner: {
    id: number;
    display_name: string;
    first_name: string;
    passport_status: PassportStatus;
    passport_number: string;
    journey_stage: string | null;
  };
  status: PassportStatus;
  journey: JourneyStage[];
  privacy_note: string;
  updated_at: string;
  has_evidence: boolean;
  parent_insight: ParentInsight | null;
  parent_insight_state: "READY" | "PENDING" | "NOT_AVAILABLE";
  // Present once the learner has evidence:
  headline?: string;
  current_signals?: {
    key: string;
    label: string;
    score: number;
    confidence: Confidence;
    evidence_count: number;
    opportunity_count: number;
  }[];
  other_signals?: PassportSignal[];
  evidence?: EvidenceSummary;
  explored_dimensions?: ExploredDimension[];
  recent_activity?: { id: number; title: string; source_label: string; created_at: string; dimensions: string[] }[];
  emerging_strengths?: EmergingStrength[];
  areas_to_explore?: string[];
  uncertainty_notes?: string[];
  next_step?: { title: string; activity_type: string; signals: string[] } | null;
  next_mission?: {
    title: string;
    short_description: string;
    time_label: string;
    focus_areas: string[];
    status: AttemptStatus;
  } | null;
}

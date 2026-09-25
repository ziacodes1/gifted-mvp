export interface EmergingStrength {
  title: string;
  reason: string;
}

export interface ProfileSynthesis {
  headline: string;
  summary: string;
  emerging_strengths: EmergingStrength[];
  exposure_gaps: string[];
  uncertainty_notes: string[];
  suggested_explorations: string[];
}

export interface NextStepRecommendation {
  title: string;
  activity_type: string;
  reason: string;
  signals_used: string[];
  intended_validation: string;
  confidence_note: string;
}

export interface ProfileInsight {
  session_id: number;
  source: "AI" | "FALLBACK";
  profile: ProfileSynthesis;
  next_step: NextStepRecommendation;
  generated_at: string;
}

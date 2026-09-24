export type QuestionType =
  | "SINGLE_CHOICE"
  | "VISUAL_CHOICE"
  | "STORY_CHOICE"
  | "SCENARIO_CHOICE"
  | "VALUE_TRADEOFF"
  | "MULTI_SELECT"
  | "PATTERN_CHOICE";

export type PuzzleStimulus =
  | { kind: "sequence"; items: string[] }
  | { kind: "shape"; cells: [number, number][] };

export interface QuestionOption {
  id: number;
  label: string;
  description: string;
  icon: string;
  image: string;
  content: { icon?: string; exclusive?: boolean; cells?: [number, number][] };
  order: number;
}

export interface Question {
  id: number;
  type: QuestionType;
  prompt: string;
  helper_text: string;
  content: { scenario?: string; stimulus?: PuzzleStimulus; min?: number; max?: number };
  order: number;
  options: QuestionOption[];
}

export type SessionStatus = "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";

export interface LatestSession {
  id: number;
  status: SessionStatus;
  progress: number;
}

export interface AssessmentListItem {
  id: number;
  title: string;
  slug: string;
  description: string;
  question_count: number;
  my_latest_session: LatestSession | null;
}

export interface AssessmentSession {
  id: number;
  status: SessionStatus;
  progress: number;
  assessment: { id: number; title: string; slug: string; description: string; question_count: number };
  questions: Question[];
  responses: Record<string, number[]>;
  total_questions: number;
  answered_count: number;
  started_at: string;
  completed_at: string | null;
}

export type SignalCategory = "INTEREST" | "APTITUDE" | "WORK_STYLE" | "VALUE" | "EXPOSURE";
export type Confidence = "LOW" | "MEDIUM" | "HIGH";

export interface SignalResult {
  key: string;
  label: string;
  category: SignalCategory;
  score: number;
  confidence: Confidence;
}

export interface LearnerSignal extends SignalResult {
  evidence_count: number;
  opportunity_count: number;
  updated_at: string;
}

export interface CompleteResult {
  session_id: number;
  status: SessionStatus;
  signals: SignalResult[];
  top_signals: SignalResult[];
  exposure_note: string;
  ai_ready: boolean;
}

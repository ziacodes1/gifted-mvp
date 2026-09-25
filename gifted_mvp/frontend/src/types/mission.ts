export type MissionStepType = "CONTEXT" | "MULTI_SELECT" | "BUDGET" | "SINGLE_CHOICE" | "REFLECTION";
export type AttemptStatus = "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";
export type MissionMatch = "RECOMMENDED" | "SUGGESTED";

export interface MissionOption {
  key: string;
  label: string;
  description?: string;
  icon?: string;
  cost?: number;
  tradeoff?: string;
}

export interface ReflectionField {
  key: string;
  label: string;
  placeholder?: string;
  required?: boolean;
  min_length?: number;
  max_length?: number;
}

export interface MissionStepContent {
  options?: MissionOption[];
  min?: number;
  max?: number;
  budget?: number;
  min_items?: number;
  voices?: { quote: string; who: string }[];
  goal?: string;
  fields?: ReflectionField[];
}

export interface MissionStep {
  id: number;
  key: string;
  type: MissionStepType;
  title: string;
  prompt: string;
  content: MissionStepContent;
  order: number;
}

export interface MissionSummary {
  id: number;
  slug: string;
  title: string;
  short_description: string;
  difficulty: "BEGINNER" | "INTERMEDIATE";
  estimated_minutes: number;
  time_label: string;
  activity_label: string;
  focus_areas: string[];
  my_attempt: { id: number; status: AttemptStatus } | null;
  match?: MissionMatch;
}

export interface MissionDetail extends Omit<MissionSummary, "my_attempt"> {
  context: string;
  steps: MissionStep[];
  intro_steps: { title: string; text: string }[];
  my_attempt?: { id: number; status: AttemptStatus } | null;
}

/** Shape stored per step. */
export type StepResponse = { acknowledged?: boolean; selected?: string | string[]; [field: string]: unknown };

export interface EvidenceDimension {
  key: string;
  label: string;
  kind: string;
  kind_label: string;
}

export interface MissionResult {
  id: number;
  title: string;
  created_at: string;
  dimensions: EvidenceDimension[];
}

export interface MissionAttempt {
  id: number;
  status: AttemptStatus;
  started_at: string;
  completed_at: string | null;
  mission: MissionDetail;
  responses: Record<string, StepResponse>;
  next_step_index: number;
  result: MissionResult | null;
  evidence_created?: boolean;
  passport?: { status: string; version: number; missions: number };
}

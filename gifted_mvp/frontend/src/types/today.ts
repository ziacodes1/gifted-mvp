export type SparkType = "REFLECTION" | "MINI_CHALLENGE" | "FACT" | "NEXT_STEP" | "DIARY_PROMPT" | "COMPANION_PROMPT" | "MISSION_NUDGE";
export type SparkAction = "diary" | "companion" | "go" | "complete";
export type SparkRoute = "companion" | "diary" | "mission" | "passport" | "assessment" | null;

export interface Spark {
  key: string;
  type: SparkType;
  status: "NEW" | "DONE" | "DISMISSED";
  route: SparkRoute;
  target: string | null;
  actions: SparkAction[];
  fact_index: number | null;
  points: number;
}

export interface Nudge {
  kind: "spark" | "badge" | "passport" | "diary_milestone" | "reward";
  params: Record<string, string | number>;
  to: string;
  at: string;
  unread: boolean;
}

export interface Today {
  day: string;
  spark: Spark;
  motivation: string;
  nudges: Nudge[];
  unread: number;
}

export type EventType =
  | "ASSESSMENT_COMPLETED"
  | "ASSESSMENT_PROGRESS"
  | "MISSION_COMPLETED"
  | "DIARY_ENTRY_CREATED"
  | "FIRST_DIARY_ENTRY"
  | "STREAK_7_DAYS"
  | "MINI_CHALLENGE";

export type RewardType = "PHYSICAL" | "COURSE" | "EVENT" | "COMMUNITY" | "MENTOR";
export type BadgeIcon = "leaf" | "star" | "book" | "compass" | "globe" | "people" | "bulb" | "mountain" | "passport";
export type BadgeTone = "green" | "gold" | "purple" | "teal";

export interface Streak {
  current: number;
  longest: number;
  active_today: boolean;
  week: { date: string; active: boolean; future: boolean }[];
  active_days_this_week: number;
  bonus_days: number;
  bonus_points: number;
  had_streak_before: boolean;
}

export interface Points {
  total_earned: number;
  available: number;
  spent: number;
  this_week: number;
}

export interface Badge {
  key: string;
  icon: BadgeIcon;
  tone: BadgeTone;
  available: boolean;
  unlocked: boolean;
  unlocked_at: string | null;
  progress: { current: number; target: number } | null;
}

export interface LeaderRow {
  rank: number | null;
  display_name: string | null;
  weekly_points: number;
  is_me: boolean;
}

export interface Leaderboard {
  week_start: string;
  top: LeaderRow[];
  me: LeaderRow;
  active_learners: number;
}

export interface Standing {
  kind: "top_percent" | "most_active" | "keep_going" | "not_yet";
  percent: number | null;
}

export interface Reward {
  key: string;
  title: string;
  description: string;
  points_required: number;
  reward_type: RewardType;
  image_key: string;
  stock_left: number | null;
  redeemed: boolean;
  points_missing: number;
  can_redeem: boolean;
}

export interface EngagementOverview {
  today: string;
  points: Points;
  streak: Streak;
  badges: Badge[];
  leaderboard: Leaderboard;
  standing: Standing;
  rewards: Reward[];
  redemptions: { reward_key: string; status: string; points_spent: number; created_at: string }[];
  recent_activity: { type: EventType; points: number; date: string }[];
}

export interface RedeemResult {
  reward_key: string;
  reward_type: RewardType;
  status: "RESERVED";
  points_spent: number;
  points: Points;
}

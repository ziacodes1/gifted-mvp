/** Ecosystem: resources, opportunities, community. Mirrors apps/ecosystem/services. */

export type Category =
  | "STEM"
  | "AI_TECH"
  | "ARTS"
  | "LEADERSHIP"
  | "ENTREPRENEURSHIP"
  | "SOCIAL_IMPACT"
  | "ENVIRONMENT"
  | "LANGUAGES"
  | "PERSONAL_DEVELOPMENT";

export type MatchLevel = "STRONG_FIT" | "WORTH_EXPLORING" | "NEW_AREA" | "EXPLORE";
export type ReasonCode = "interest" | "work_style" | "value" | "aptitude" | "evidence" | "exposure_gap" | "emerging" | "new_area";

export interface MatchReason {
  code: ReasonCode;
  signal: string | null;
  label: string;
}

export interface Match {
  level: MatchLevel;
  reasons: MatchReason[];
}

export interface Organization {
  slug: string;
  name: string;
  type: string;
  short_description: string;
  website_url: string;
  city: string;
  country: string;
  verified: boolean;
  is_demo: boolean;
}

export type ResourceType = "ARTICLE" | "VIDEO" | "TOOLKIT" | "COURSE";
export type ProgressStatus = "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";

export interface ResourceCard {
  slug: string;
  title: string;
  short_description: string;
  type: ResourceType;
  category: Category;
  cover_key: string;
  duration_minutes: number;
  difficulty: "BEGINNER" | "INTERMEDIATE" | "ADVANCED";
  is_external: boolean;
  organization: Organization;
  featured: boolean;
  saved: boolean;
  status: ProgressStatus;
  match: Match;
}

export interface ResourceDetail extends ResourceCard {
  content: { intro?: string; points?: string[]; try_this?: string };
  external_url: string;
  produces_evidence: boolean;
  evidence_recorded: boolean;
  tracks_progress: boolean;
  paths: { slug: string; title: string }[];
  has_signals: boolean;
}

export interface LearningPathSummary {
  slug: string;
  title: string;
  description: string;
  category: Category;
  cover_key: string;
  difficulty: string;
  organization: Organization;
  resource_count: number;
  duration_minutes: number;
  completed_count: number;
  next_resource: string | null;
  items?: ResourceCard[];
}

export interface ResourceList {
  has_signals: boolean;
  featured_path: LearningPathSummary | null;
  items: ResourceCard[];
}

export type ResourceAction = "save" | "unsave" | "open" | "start" | "complete" | "reset";

export type OpportunityType =
  | "COMPETITION"
  | "HACKATHON"
  | "FELLOWSHIP"
  | "CAMP"
  | "SCHOLARSHIP"
  | "EVENT"
  | "INTERNSHIP"
  | "VOLUNTEERING"
  | "PROGRAM"
  | "WORKSHOP";
export type Mode = "ONLINE" | "IN_PERSON" | "HYBRID";
export type DeadlineStatus = "OPEN" | "CLOSING_SOON" | "CLOSED" | "ROLLING" | "NOT_YET_OPEN";
export type InteractionState = "NONE" | "VIEWED" | "SAVED" | "APPLICATION_LINK_OPENED";

export interface Eligibility {
  age: { min: number | null; max: number | null; status: "CHECK" | "ANY" };
  location: { status: "ANYWHERE" | "ONLINE_REGION" | "ON_SITE"; mode: Mode; city: string; country: string };
  deadline: { status: DeadlineStatus; days_left: number | null; opens?: string };
  open_now: boolean;
}

export interface OpportunityCard {
  slug: string;
  title: string;
  short_description: string;
  type: OpportunityType;
  category: Category;
  mode: Mode;
  city: string;
  country: string;
  global_available: boolean;
  age_min: number | null;
  age_max: number | null;
  application_deadline: string | null;
  program_start: string | null;
  program_end: string | null;
  cover_key: string;
  organization: Organization;
  featured: boolean;
  saved: boolean;
  state: InteractionState;
  match: Match;
  eligibility: Eligibility;
}

export interface OpportunityDetail extends OpportunityCard {
  description: string;
  skills: string[];
  requirements: string[];
  faqs: { q: string; a: string }[];
  application_url: string;
  application_open_at: string | null;
  has_signals: boolean;
}

export interface OpportunityList {
  has_signals: boolean;
  featured: OpportunityCard | null;
  items: OpportunityCard[];
  facets: { countries: string[]; types: OpportunityType[] };
}

export interface OpportunityFilters {
  category?: Category;
  mode?: "ONLINE" | "IN_PERSON";
  type?: OpportunityType;
  country?: string;
  age?: number;
  deadline?: "closing_soon" | "all";
  q?: string;
  saved?: boolean;
}

export type OpportunityAction = "save" | "unsave" | "view" | "open_link";

export interface CircleCard {
  slug: string;
  name: string;
  description: string;
  category: Category;
  cover_key: string;
  icon_key: string;
  member_count: number;
  joined: boolean;
  reason: { code: "interest" | "emerging"; signal: string; label: string } | null;
}

export type PostType = "SHARE" | "QUESTION" | "IDEA" | "ACHIEVEMENT";

export interface CommunityPost {
  id: number;
  author: "you" | null;
  author_name: string | null;
  circle: { slug: string; name: string };
  body: string;
  post_type: PostType;
  status: "PENDING" | "APPROVED" | "REJECTED";
  mine: boolean;
  created_at: string;
}

export interface CommunityEvent {
  id: number;
  title: string;
  description: string;
  start_at: string;
  end_at: string | null;
  mode: Mode;
  location: string;
  external_url: string;
  circle: { slug: string; name: string } | null;
  organization: Organization | null;
}

export interface CommunityOverview {
  has_signals: boolean;
  suggested: CircleCard[];
  my_circles: CircleCard[];
  circles: CircleCard[];
  feed: CommunityPost[];
  events: CommunityEvent[];
}

export type ReportReason = "UNKIND" | "UNSAFE" | "SPAM" | "OTHER";

export interface ForYou {
  has_signals: boolean;
  resource: ResourceCard | null;
  opportunity: OpportunityCard | null;
  circle: CircleCard | null;
}

export type MessageRole = "USER" | "ASSISTANT";

export interface CompanionMessage {
  id: number;
  role: MessageRole;
  content: string;
  created_at: string;
}

export interface ConversationSummary {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Conversation extends ConversationSummary {
  messages: CompanionMessage[];
}

export interface SendResult {
  conversation: ConversationSummary;
  user_message: CompanionMessage;
  assistant_message: CompanionMessage;
}

/** Prompt text lives in the frontend locales (`companion.prompts.<key>`); params are localized by the backend. */
export interface SuggestedPrompt {
  key: string;
  params: Record<string, string>;
}

export interface CompanionAbout {
  first_name: string;
  passport_status: "EMPTY" | "EMERGING" | "GROWING";
  journey_stage: string | null;
  interests: string[];
  values: string[];
  missions_completed: number;
  next_exploration: string | null;
}

export interface CompanionOverview {
  about: CompanionAbout;
  suggested_prompts: SuggestedPrompt[];
}

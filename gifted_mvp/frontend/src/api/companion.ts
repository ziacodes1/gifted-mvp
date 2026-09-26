import { api } from "./client";
import type { CompanionOverview, Conversation, ConversationSummary, SendResult } from "../types/companion";

export const companionApi = {
  async overview(): Promise<CompanionOverview> {
    const { data } = await api.get<CompanionOverview>("/companion/overview/");
    return data;
  },
  /** Conversations that have at least one message, newest first. */
  async conversations(): Promise<ConversationSummary[]> {
    const { data } = await api.get<ConversationSummary[]>("/companion/conversations/");
    return data;
  },
  /** New chat (the server reuses the newest one if it is still empty). */
  async create(): Promise<Conversation> {
    const { data } = await api.post<Conversation>("/companion/conversations/");
    return data;
  },
  async conversation(id: number): Promise<Conversation> {
    const { data } = await api.get<Conversation>(`/companion/conversations/${id}/`);
    return data;
  },
  /** Idempotent per clientId: a retry returns the stored turn instead of a second reply.
   * Rejects with HTTP 503 when the Companion can't answer right now (nothing is stored). */
  async send(id: number, content: string, clientId: string): Promise<SendResult> {
    const { data } = await api.post<SendResult>(`/companion/conversations/${id}/messages/`, {
      content,
      client_id: clientId,
    });
    return data;
  },
};

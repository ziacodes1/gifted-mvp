import { api } from "./client";
import type { ProfileInsight } from "../types/ai";

export const aiApi = {
  /** Idempotent get-or-generate. Omit sessionId to use the latest completed session.
   * The backend reads trusted signals itself — never send scores from here.
   * The output language follows the Accept-Language header (one saved insight per language). */
  async profileSynthesis(sessionId?: number): Promise<ProfileInsight> {
    const { data } = await api.post<ProfileInsight>(
      "/ai/profile-synthesis/",
      sessionId ? { session_id: sessionId } : {},
    );
    return data;
  },
};

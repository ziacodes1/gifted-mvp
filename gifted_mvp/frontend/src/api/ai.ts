import { api } from "./client";
import type { ProfileInsight } from "../types/ai";

export const aiApi = {
  /** Idempotent get-or-generate. Omit sessionId to use the latest completed session.
   * The backend reads trusted signals itself — never send scores from here. */
  async profileSynthesis(sessionId?: number): Promise<ProfileInsight> {
    const { data } = await api.post<ProfileInsight>(
      "/ai/profile-synthesis/",
      sessionId ? { session_id: sessionId } : {},
    );
    return data;
  },
};

import { api } from "./client";
import type { ParentChildSummary, ParentInsight, ParentOverview } from "../types/parent";

export const parentApi = {
  async children(): Promise<ParentChildSummary[]> {
    const { data } = await api.get<ParentChildSummary[]>("/parent/children/");
    return data;
  },
  /** One aggregate for the dashboard and insights page. Never triggers AI. */
  async overview(learnerId: number): Promise<ParentOverview> {
    const { data } = await api.get<ParentOverview>(`/parent/children/${learnerId}/overview/`);
    return data;
  },
  /** Idempotent get-or-generate for the current evidence version. */
  async insight(learnerId: number): Promise<ParentInsight | null> {
    const { data } = await api.post<{ parent_insight: ParentInsight | null }>(`/parent/children/${learnerId}/insight/`);
    return data.parent_insight;
  },
};

import { api } from "./client";
import type { EngagementOverview, RedeemResult } from "../types/engagement";

export const engagementApi = {
  async overview(): Promise<EngagementOverview> {
    const { data } = await api.get<EngagementOverview>("/engagement/overview/");
    return data;
  },
  /** Rejects with 400 {error: {detail: code}}: inactive | already_redeemed | out_of_stock | not_enough_points. */
  async redeem(key: string): Promise<RedeemResult> {
    const { data } = await api.post<RedeemResult>(`/engagement/rewards/${key}/redeem/`);
    return data;
  },
};

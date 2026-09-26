import { api } from "./client";
import type { Today } from "../types/today";

export const todayApi = {
  /** Today's Spark + motivation + in-app nudges. One request, no AI call. */
  async get(): Promise<Today> {
    const { data } = await api.get<Today>("/today/");
    return data;
  },
  /** complete (mini challenges; idempotent) · dismiss · restore. Returns the updated Today. */
  async act(sparkKey: string, action: "complete" | "dismiss" | "restore"): Promise<Today> {
    const { data } = await api.post<Today>("/today/spark/", { spark_key: sparkKey, action });
    return data;
  },
  async markSeen(): Promise<void> {
    await api.post("/today/nudges/seen/");
  },
};

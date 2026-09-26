import { isAxiosError } from "axios";
import { api } from "./client";
import type { MissionAttempt, MissionDetail, MissionSummary, StepResponse } from "../types/mission";

export const missionsApi = {
  async list(): Promise<MissionSummary[]> {
    const { data } = await api.get<MissionSummary[]>("/missions/");
    return data;
  },
  async detail(slug: string): Promise<MissionDetail> {
    const { data } = await api.get<MissionDetail>(`/missions/${slug}/`);
    return data;
  },
  /** Resumes the learner's existing attempt if there is one. */
  async start(slug: string): Promise<MissionAttempt> {
    const { data } = await api.post<MissionAttempt>(`/missions/${slug}/start/`);
    return data;
  },
  async attempt(id: number): Promise<MissionAttempt> {
    const { data } = await api.get<MissionAttempt>(`/mission-attempts/${id}/`);
    return data;
  },
  async answer(id: number, stepId: number, response: StepResponse): Promise<MissionAttempt> {
    const { data } = await api.post<MissionAttempt>(`/mission-attempts/${id}/answer/`, {
      step_id: stepId,
      response,
    });
    return data;
  },
  /** Idempotent on the server. */
  async complete(id: number): Promise<MissionAttempt> {
    const { data } = await api.post<MissionAttempt>(`/mission-attempts/${id}/complete/`);
    return data;
  },
};

/** Pull a human message out of the API's `{error: {detail}}` envelope (callers pass a localized fallback). */
export function apiErrorMessage(err: unknown, fallback: string): string {
  if (!isAxiosError(err)) return fallback;
  const detail = (err.response?.data as { error?: { detail?: unknown } } | undefined)?.error?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && typeof detail[0] === "string") return detail[0];
  if (detail && typeof detail === "object") {
    const first = Object.values(detail)[0];
    if (typeof first === "string") return first;
    if (Array.isArray(first) && typeof first[0] === "string") return first[0];
  }
  return fallback;
}

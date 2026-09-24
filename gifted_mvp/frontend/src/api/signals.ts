import { api } from "./client";
import type { LearnerSignal } from "../types/assessment";

interface Paginated<T> {
  count: number;
  results: T[];
}

export const signalsApi = {
  async mine(): Promise<LearnerSignal[]> {
    const { data } = await api.get<Paginated<LearnerSignal>>("/signals/me/");
    return data.results;
  },
};

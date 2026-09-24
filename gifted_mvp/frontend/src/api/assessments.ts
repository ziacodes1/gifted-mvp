import { api } from "./client";
import type { AssessmentListItem, AssessmentSession, CompleteResult } from "../types/assessment";

interface Paginated<T> {
  count: number;
  results: T[];
}

export const assessmentsApi = {
  async list(): Promise<AssessmentListItem[]> {
    const { data } = await api.get<Paginated<AssessmentListItem>>("/assessments/");
    return data.results;
  },
  async start(assessmentId: number): Promise<AssessmentSession> {
    const { data } = await api.post<AssessmentSession>(`/assessments/${assessmentId}/start/`);
    return data;
  },
  async getSession(sessionId: number): Promise<AssessmentSession> {
    const { data } = await api.get<AssessmentSession>(`/assessment-sessions/${sessionId}/`);
    return data;
  },
  async answer(sessionId: number, questionId: number, optionIds: number[]) {
    const { data } = await api.post(`/assessment-sessions/${sessionId}/answer/`, {
      question_id: questionId,
      option_ids: optionIds,
    });
    return data as { progress: number; answered_count: number; total_questions: number };
  },

  async complete(sessionId: number): Promise<CompleteResult> {
    const { data } = await api.post<CompleteResult>(`/assessment-sessions/${sessionId}/complete/`);
    return data;
  },
};

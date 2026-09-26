import { api } from "./client";
import type {
  CompanionDraft,
  DiaryEntry,
  DiaryEntryInput,
  DiaryEntrySummary,
  DiaryOverview,
  DiaryPhoto,
  Paginated,
} from "../types/diary";

export const diaryApi = {
  async overview(): Promise<DiaryOverview> {
    const { data } = await api.get<DiaryOverview>("/diary/overview/");
    return data;
  },
  async list(params: { source?: "COMPANION" | "MANUAL"; page?: number; page_size?: number } = {}): Promise<Paginated<DiaryEntrySummary>> {
    const { data } = await api.get<Paginated<DiaryEntrySummary>>("/diary/entries/", { params });
    return data;
  },
  async entry(id: number): Promise<DiaryEntry> {
    const { data } = await api.get<DiaryEntry>(`/diary/entries/${id}/`);
    return data;
  },
  /** With companion_message_id the server returns the existing entry (200) if that moment was already saved. */
  async create(input: DiaryEntryInput): Promise<DiaryEntry> {
    const { data } = await api.post<DiaryEntry>("/diary/entries/", input);
    return data;
  },
  async update(id: number, input: DiaryEntryInput): Promise<DiaryEntry> {
    const { data } = await api.patch<DiaryEntry>(`/diary/entries/${id}/`, input);
    return data;
  },
  async remove(id: number): Promise<void> {
    await api.delete(`/diary/entries/${id}/`);
  },
  async addPhoto(entryId: number, file: File, caption = ""): Promise<DiaryPhoto> {
    const form = new FormData();
    form.append("file", file);
    form.append("caption", caption);
    const { data } = await api.post<DiaryPhoto>(`/diary/entries/${entryId}/attachments/`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
  async updatePhoto(id: number, caption: string): Promise<DiaryPhoto> {
    const { data } = await api.patch<DiaryPhoto>(`/diary/attachments/${id}/`, { caption });
    return data;
  },
  async removePhoto(id: number): Promise<void> {
    await api.delete(`/diary/attachments/${id}/`);
  },
  /** Photos are private: fetched with the learner's token, shown via an object URL. */
  async photoBlob(id: number): Promise<Blob> {
    const { data } = await api.get<Blob>(`/diary/attachments/${id}/`, { responseType: "blob" });
    return data;
  },
  /** After an explicit "Add to My Diary": an editor prefill from the student's own message (nothing saved). */
  async companionDraft(messageId: number): Promise<CompanionDraft> {
    const { data } = await api.post<CompanionDraft>("/diary/companion-draft/", { message_id: messageId });
    return data;
  },
};

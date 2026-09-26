export type Mood = "very_low" | "low" | "neutral" | "good" | "great";
export const MOODS: Mood[] = ["very_low", "low", "neutral", "good", "great"];

export type StickerId = "leaf" | "flower" | "star" | "spark" | "heart" | "sun" | "sprout" | "note_grow";
export const STICKER_IDS: StickerId[] = ["leaf", "flower", "star", "spark", "heart", "sun", "sprout", "note_grow"];
export const STICKER_SLOTS = 6;
export const MAX_PHOTOS = 4;
export const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
export const MAX_TAGS = 8;

export interface PlacedSticker {
  id: StickerId;
  slot: number;
}

export interface DiaryPhoto {
  id: number;
  caption: string;
  width: number;
  height: number;
}

export interface DiaryEntrySummary {
  id: number;
  title: string;
  excerpt: string;
  mood: Mood | null;
  entry_date: string;
  source: "MANUAL" | "COMPANION";
  tags: string[];
  stickers: PlacedSticker[];
  cover_photo: DiaryPhoto | null;
  photo_count: number;
  updated_at: string;
}

export interface DiaryEntry extends DiaryEntrySummary {
  body: string;
  photos: DiaryPhoto[];
  created_at: string;
  companion_message_id: number | null;
}

export interface DiaryEntryInput {
  title?: string;
  body?: string;
  mood?: Mood | "";
  tags?: string[];
  stickers?: PlacedSticker[];
  entry_date?: string;
  companion_message_id?: number;
}

export interface PendingMoment {
  assistant_message_id: number;
  student_message_id: number;
  excerpt: string;
  created_at: string;
}

export interface DiaryOverview {
  pages_filled: number;
  page_target: number;
  photo_count: number;
  last_entry_at: string | null;
  recent_entries: DiaryEntrySummary[];
  book_pages: DiaryEntrySummary[];
  mood_week: { date: string; mood: Mood | null }[];
  pending_moment: PendingMoment | null;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type CompanionDraft =
  | { existing_entry_id: number }
  | {
      existing_entry_id: null;
      draft: { title: string; body: string; entry_date: string; source: "COMPANION"; companion_message_id: number };
    };

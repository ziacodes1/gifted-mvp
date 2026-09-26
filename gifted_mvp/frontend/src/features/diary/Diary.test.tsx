import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { DiaryEntry, DiaryEntrySummary, DiaryOverview } from "../../types/diary";

vi.mock("../../api/diary", () => ({
  diaryApi: {
    overview: vi.fn(),
    list: vi.fn(),
    entry: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    remove: vi.fn(),
    addPhoto: vi.fn(),
    updatePhoto: vi.fn(),
    removePhoto: vi.fn(),
    photoBlob: vi.fn(async () => new Blob(["x"], { type: "image/webp" })),
    companionDraft: vi.fn(),
  },
}));
vi.mock("../../api/companion", () => ({ companionApi: { dismissDiaryOffer: vi.fn() } }));

import { diaryApi } from "../../api/diary";
import i18n, { setLanguage } from "../../i18n";
import { DiaryEntryRoute } from "../../pages/student/DiaryEntryPage";
import { DiaryPage } from "../../pages/student/DiaryPage";

const api = vi.mocked(diaryApi);
const TODAY = "2026-09-24";
const UZ_BODY = "Bugun men do‘stlarim bilan tog‘ga chiqdim va juda xursand bo‘ldim.";

function summary(id: number, over: Partial<DiaryEntrySummary> = {}): DiaryEntrySummary {
  return {
    id,
    title: `Page ${id}`,
    excerpt: `Words of page ${id}`,
    mood: null,
    entry_date: TODAY,
    source: "MANUAL",
    tags: [],
    stickers: [],
    cover_photo: null,
    photo_count: 0,
    updated_at: TODAY,
    ...over,
  };
}

function detail(id: number, over: Partial<DiaryEntry> = {}): DiaryEntry {
  return { ...summary(id), body: `Words of page ${id}`, photos: [], created_at: TODAY, companion_message_id: null, ...over };
}

const EMPTY_OVERVIEW: DiaryOverview = {
  pages_filled: 0,
  page_target: 100,
  photo_count: 0,
  last_entry_at: null,
  recent_entries: [],
  book_pages: [],
  mood_week: Array.from({ length: 7 }, (_, i) => ({ date: `2026-09-2${i + 1}`, mood: null })),
  pending_moment: null,
};

function ShowLocation() {
  const loc = useLocation();
  return <p>at {loc.pathname + loc.search}</p>;
}

function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <I18nextProvider i18n={i18n}>
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/app/diary" element={<DiaryPage />} />
            <Route path="/app/diary/new" element={<DiaryEntryRoute />} />
            <Route path="/app/diary/:id" element={<DiaryEntryRoute />} />
            <Route path="*" element={<ShowLocation />} />
          </Routes>
          <ShowLocation />
        </MemoryRouter>
      </QueryClientProvider>
    </I18nextProvider>,
  );
}

beforeEach(async () => {
  vi.clearAllMocks();
  await setLanguage("en");
  api.overview.mockResolvedValue(EMPTY_OVERVIEW);
  URL.createObjectURL = vi.fn(() => "blob:preview");
});
afterEach(cleanup);

describe("Diary home", () => {
  it("empty state invites the first entry", async () => {
    renderAt("/app/diary");
    expect(await screen.findByText("Your story starts here.")).toBeTruthy();
    expect(screen.getByText("0 of 100 pages filled")).toBeTruthy();
    expect(screen.getByText("Create your first entry").closest("a")?.getAttribute("href")).toBe("/app/diary/new");
    expect(screen.getByText(/Your diary is private unless a future feature/)).toBeTruthy();
  });

  it("renders real pages, progress, recent entries and this week's moods", async () => {
    const entries = [
      summary(3, { title: "A proud day", mood: "great", source: "COMPANION" }),
      summary(2, { title: "Rainy walk" }),
      summary(1, { title: "First page" }),
    ];
    api.overview.mockResolvedValue({
      ...EMPTY_OVERVIEW,
      pages_filled: 3,
      recent_entries: entries,
      book_pages: entries,
      mood_week: EMPTY_OVERVIEW.mood_week.map((d, i) => (i === 3 ? { ...d, mood: "great" } : d)),
    });
    renderAt("/app/diary");
    expect(await screen.findByText("3 of 100 pages filled")).toBeTruthy();
    expect(screen.getByText("97 more pages to your brighter story…")).toBeTruthy();
    expect(screen.getAllByText("A proud day").length).toBeGreaterThanOrEqual(2); // book + recent list
    expect(screen.getByText("From AI Companion")).toBeTruthy();
    expect(screen.getAllByText("Great").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Open my diary").closest("a")?.getAttribute("href")).toBe("/app/diary/3");
  });
});

describe("Diary editor", () => {
  it("creates an entry with mood, tag, sticker and emoji, then opens it", async () => {
    api.create.mockResolvedValue(detail(7));
    renderAt("/app/diary/new");
    fireEvent.change(screen.getByLabelText("Give this page a title…"), { target: { value: "Science fair" } });
    fireEvent.change(screen.getByLabelText("Dear diary…"), { target: { value: "We won second place" } });
    fireEvent.click(screen.getByRole("radio", { name: "Good" }));
    const tag = screen.getByLabelText("Add a tag, then press Enter");
    fireEvent.change(tag, { target: { value: "#school" } });
    fireEvent.keyDown(tag, { key: "Enter" });
    fireEvent.click(screen.getByText("Stickers"));
    fireEvent.click(screen.getByRole("button", { name: "Leaf" }));
    expect(screen.getByRole("button", { name: "Remove sticker: Leaf" })).toBeTruthy();
    fireEvent.click(screen.getByText("Emoji"));
    fireEvent.click(screen.getByRole("button", { name: "🌟" }));

    fireEvent.click(screen.getByText("Save entry"));
    await waitFor(() => expect(api.create).toHaveBeenCalledTimes(1));
    expect(api.create.mock.calls[0][0]).toMatchObject({
      title: "Science fair",
      mood: "good",
      tags: ["school"],
      stickers: [{ id: "leaf", slot: 0 }],
      companion_message_id: undefined,
    });
    expect(api.create.mock.calls[0][0].body).toContain("🌟");
    expect(await screen.findByText("at /app/diary/7")).toBeTruthy();
  });

  it("does not save an empty page", async () => {
    renderAt("/app/diary/new");
    fireEvent.click(screen.getByText("Save entry"));
    expect(await screen.findByText("Write a title or a few words before saving.")).toBeTruthy();
    expect(api.create).not.toHaveBeenCalled();
  });

  it("edits an existing entry", async () => {
    api.entry.mockResolvedValue(detail(5, { title: "Old title", body: "Old words", mood: "low" }));
    api.update.mockImplementation(async (_id, input) => detail(5, { ...input, mood: "low" } as Partial<DiaryEntry>));
    renderAt("/app/diary/5");
    const body = (await screen.findByLabelText("Dear diary…")) as HTMLTextAreaElement;
    expect(body.value).toBe("Old words");
    expect(screen.getByRole("radio", { name: "Low" }).getAttribute("aria-checked")).toBe("true");
    fireEvent.change(body, { target: { value: "New words" } });
    fireEvent.click(screen.getByText("Save entry"));
    await waitFor(() => expect(api.update).toHaveBeenCalledWith(5, expect.objectContaining({ body: "New words", title: "Old title" })));
    expect(await screen.findByText("Saved to your diary")).toBeTruthy();
  });

  it("photo control validates type/size and uploads queued photos after the first save", async () => {
    api.create.mockResolvedValue(detail(8));
    api.addPhoto.mockResolvedValue({ id: 1, caption: "", width: 10, height: 10 });
    renderAt("/app/diary/new");
    const input = screen.getByTestId("photo-input") as HTMLInputElement;

    fireEvent.change(input, { target: { files: [new File(["#!"], "run.sh", { type: "text/x-sh" })] } });
    expect(await screen.findByText("Please choose a JPEG, PNG or WebP image.")).toBeTruthy();
    const big = new File(["x"], "big.png", { type: "image/png" });
    Object.defineProperty(big, "size", { value: 6 * 1024 * 1024 });
    fireEvent.change(input, { target: { files: [big] } });
    expect(await screen.findByText("That photo is larger than 5 MB.")).toBeTruthy();

    const ok = new File(["png"], "me.png", { type: "image/png" });
    await act(async () => fireEvent.change(input, { target: { files: [ok] } }));
    expect(screen.getAllByRole("button", { name: "Remove photo" }).length).toBe(1);
    fireEvent.change(screen.getByLabelText("Dear diary…"), { target: { value: "A day out" } });
    fireEvent.click(screen.getByText("Save entry"));
    await waitFor(() => expect(api.addPhoto).toHaveBeenCalledWith(8, ok, ""));
  });

  it("a Companion draft is prefilled from the student's words and saved only on Save", async () => {
    api.companionDraft.mockResolvedValue({
      existing_entry_id: null,
      draft: { title: "I presented today", body: "I presented today. I felt proud.", entry_date: TODAY, source: "COMPANION", companion_message_id: 42 },
    });
    api.create.mockResolvedValue(detail(9, { source: "COMPANION" }));
    renderAt("/app/diary/new?from=42");
    expect(await screen.findByText(/Only your own words were copied/)).toBeTruthy();
    expect((screen.getByLabelText("Dear diary…") as HTMLTextAreaElement).value).toBe("I presented today. I felt proud.");
    expect(api.create).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Save entry"));
    await waitFor(() => expect(api.create).toHaveBeenCalledWith(expect.objectContaining({ companion_message_id: 42 })));
  });

  it("an already-saved Companion moment opens its existing page", async () => {
    api.companionDraft.mockResolvedValue({ existing_entry_id: 11 });
    api.entry.mockResolvedValue(detail(11));
    renderAt("/app/diary/new?from=42");
    expect(await screen.findByText("at /app/diary/11")).toBeTruthy();
    expect(api.create).not.toHaveBeenCalled();
  });

  it("switching language translates the UI but never the student's writing", async () => {
    api.entry.mockResolvedValue(detail(6, { title: "Tog‘da", body: UZ_BODY }));
    renderAt("/app/diary/6");
    const body = (await screen.findByLabelText("Dear diary…")) as HTMLTextAreaElement;
    await act(async () => setLanguage("ru"));
    expect(screen.getByText("Сохранить запись")).toBeTruthy();
    expect(screen.getByRole("radio", { name: "Отлично" })).toBeTruthy();
    expect((screen.getByLabelText("Дорогой дневник…") as HTMLTextAreaElement).value).toBe(UZ_BODY);
    expect((screen.getByLabelText("Дай странице название…") as HTMLInputElement).value).toBe("Tog‘da");
    await act(async () => setLanguage("uz"));
    expect(screen.getByText("Saqlash")).toBeTruthy();
    expect(screen.getByText("24 sen 2026 · Pay")).toBeTruthy(); // Uzbek date names, not "2026 M09 24"
    expect(body.value).toBe(UZ_BODY);
  });
});

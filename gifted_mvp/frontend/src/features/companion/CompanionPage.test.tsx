import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { CompanionOverview, Conversation, SendResult } from "../../types/companion";

vi.mock("../../api/companion", () => ({
  companionApi: {
    overview: vi.fn(),
    conversations: vi.fn(),
    create: vi.fn(),
    conversation: vi.fn(),
    send: vi.fn(),
    dismissDiaryOffer: vi.fn(),
  },
}));
vi.mock("../../api/diary", () => ({
  diaryApi: { list: vi.fn(async () => ({ count: 0, next: null, previous: null, results: [] })) },
}));
vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({ user: { full_name: "Ada Lovelace", email: "ada@test.dev", role: "STUDENT" } }),
}));

import { companionApi } from "../../api/companion";
import i18n, { setLanguage } from "../../i18n";
import { CompanionPage } from "../../pages/student/CompanionPage";

const api = vi.mocked(companionApi);
const NOW = "2026-09-26T10:00:00Z";

const OVERVIEW: CompanionOverview = {
  about: {
    first_name: "Ada",
    passport_status: "GROWING",
    journey_stage: "Explore",
    interests: ["Art & Design"],
    values: ["Discovering new things"],
    missions_completed: 1,
    next_exploration: "Create a one-page visual idea",
  },
  suggested_prompts: [
    { key: "reflect_mission", params: { mission: "Design a Better School Bag" } },
    { key: "explore_next", params: {} },
  ],
};

const empty = (id: number): Conversation => ({ id, title: "", created_at: NOW, updated_at: NOW, messages: [] });

function reply(id: number, content: string, answer = "Here is one idea to explore."): SendResult {
  return {
    conversation: { id, title: content, created_at: NOW, updated_at: NOW },
    user_message: { id: id * 10 + 1, role: "USER", content, created_at: NOW },
    assistant_message: { id: id * 10 + 2, role: "ASSISTANT", content: answer, created_at: NOW },
  };
}

function ShowLocation() {
  const loc = useLocation();
  return <p>at {loc.pathname + loc.search}</p>;
}

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <I18nextProvider i18n={i18n}>
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/app/companion"]}>
          <Routes>
            <Route path="/app/companion" element={<CompanionPage />} />
            <Route path="/app/diary/new" element={<ShowLocation />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </I18nextProvider>,
  );
}

beforeEach(async () => {
  vi.resetAllMocks();
  await setLanguage("en");
  api.overview.mockResolvedValue(OVERVIEW);
  api.conversations.mockResolvedValue([]);
  api.create.mockResolvedValue(empty(1));
  api.conversation.mockImplementation(async (id: number) => empty(id));
});
afterEach(cleanup);

describe("AI Companion page", () => {
  it("renders the chat, About you, suggested prompts and the privacy notice", async () => {
    renderPage();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toContain("Here for today,");
    expect(await screen.findByText("Help me reflect on my mission “Design a Better School Bag”")).toBeTruthy();
    expect(screen.getByText(/Hi Ada! I’m your Gifted Companion/)).toBeTruthy();
    expect(screen.getByText("Stage: Explore")).toBeTruthy();
    expect(screen.getByText("1 mission completed")).toBeTruthy();
    expect(screen.getByText("Your conversations with your AI Companion are private and are not shown to parents.")).toBeTruthy();
    expect(await screen.findByText(/When something feels worth keeping/)).toBeTruthy(); // no diary moments yet
  });

  it("a suggested prompt sends that message and shows the reply", async () => {
    api.send.mockImplementation(async (id, content) => reply(id, content));
    renderPage();
    fireEvent.click(await screen.findByText("What could I explore next?"));
    expect(await screen.findByText("Here is one idea to explore.")).toBeTruthy();
    expect(api.create).toHaveBeenCalledTimes(1);
    expect(api.send).toHaveBeenCalledWith(1, "What could I explore next?", expect.any(String));
  });

  it("shows a thinking state and blocks a second send while waiting", async () => {
    let resolve!: (r: SendResult) => void;
    api.send.mockImplementation((id, content) => new Promise((r) => (resolve = (x) => r(x ?? reply(id, content)))));
    renderPage();
    const box = screen.getByLabelText("Tell me what’s on your mind…");
    fireEvent.change(box, { target: { value: "I have a test on Friday" } });
    fireEvent.keyDown(box, { key: "Enter" });

    expect(await screen.findByText("Thinking it through…")).toBeTruthy();
    fireEvent.click(screen.getByText("What could I explore next?"));
    fireEvent.change(box, { target: { value: "hello?" } });
    expect((screen.getByLabelText("Send") as HTMLButtonElement).disabled).toBe(true);
    expect(api.send).toHaveBeenCalledTimes(1);

    await act(async () => resolve(reply(1, "I have a test on Friday", "Let’s make a small plan.")));
    expect(await screen.findByText("Let’s make a small plan.")).toBeTruthy();
    expect(screen.queryByText("Thinking it through…")).toBeNull();
  });

  it("a failed reply shows a calm error and retries with the same client id", async () => {
    api.send.mockRejectedValueOnce(new Error("503")).mockImplementation(async (id, content) => reply(id, content));
    renderPage();
    fireEvent.click(await screen.findByText("What could I explore next?"));
    expect(await screen.findByText("I couldn’t respond just now. Try again in a moment.")).toBeTruthy();
    fireEvent.click(screen.getByText("Try again"));
    expect(await screen.findByText("Here is one idea to explore.")).toBeTruthy();
    expect(api.send.mock.calls[0][2]).toBe(api.send.mock.calls[1][2]);
  });

  it("New chat opens a fresh conversation", async () => {
    api.conversations.mockResolvedValue([{ id: 7, title: "Old chat", created_at: NOW, updated_at: NOW }]);
    api.conversation.mockImplementation(async (id: number) =>
      id === 7 ? { ...empty(7), title: "Old chat", messages: [reply(7, "Old question", "Old answer").assistant_message] } : empty(id),
    );
    api.create.mockResolvedValue(empty(8));
    renderPage();
    expect(await screen.findByText("Old answer")).toBeTruthy();
    fireEvent.click(screen.getByText("New chat"));
    await waitFor(() => expect(screen.queryByText("Old answer")).toBeNull());
    expect(screen.getByText(/Hi Ada! I’m your Gifted Companion/)).toBeTruthy();
    expect(api.create).toHaveBeenCalledTimes(1);
  });

  it("switches the whole page to Uzbek and Russian", async () => {
    renderPage();
    await screen.findByText("What could I explore next?");
    await act(async () => setLanguage("uz"));
    expect(screen.getByText("Yangi suhbat")).toBeTruthy();
    expect(screen.getByText("Keyin nimani o‘rganib ko‘rsam bo‘ladi?")).toBeTruthy();
    expect(screen.getByText("AI hamroh bilan suhbatlaringiz shaxsiy va ota-onalarga ko‘rsatilmaydi.")).toBeTruthy();
    await act(async () => setLanguage("ru"));
    expect(screen.getByText("Новый чат")).toBeTruthy();
    expect(screen.getByText("Что мне исследовать дальше?")).toBeTruthy();
    expect(screen.getByText("1 миссия выполнена")).toBeTruthy();
  });
});

describe("Add to My Diary offer", () => {
  const offered = (): Conversation => ({
    ...empty(5),
    title: "t",
    messages: [
      { id: 51, role: "USER", content: "I finally presented in class and felt proud.", created_at: NOW },
      {
        id: 52,
        role: "ASSISTANT",
        content: "That took courage.",
        created_at: NOW,
        diary: { offer: "OFFERED", student_message_id: 51, entry_id: null },
      },
    ],
  });

  beforeEach(() => {
    api.conversations.mockResolvedValue([{ id: 5, title: "t", created_at: NOW, updated_at: NOW }]);
    api.conversation.mockResolvedValue(offered());
  });

  it("offers, and Add to My Diary opens the editor with that student message — nothing is saved here", async () => {
    renderPage();
    expect(await screen.findByText("This sounds meaningful — would you like to add it to your diary?")).toBeTruthy();
    fireEvent.click(screen.getByText("Add to My Diary"));
    expect(await screen.findByText("at /app/diary/new?from=51")).toBeTruthy();
    expect(api.dismissDiaryOffer).not.toHaveBeenCalled();
  });

  it("Keep only in chat hides the offer", async () => {
    api.dismissDiaryOffer.mockResolvedValue(undefined);
    renderPage();
    fireEvent.click(await screen.findByText("Keep only in chat"));
    await waitFor(() => expect(screen.queryByText("Add to My Diary")).toBeNull());
    expect(api.dismissDiaryOffer).toHaveBeenCalledWith(52);
  });

  it("a saved moment links to its diary page instead of offering again", async () => {
    const saved = offered();
    saved.messages[1].diary = { offer: "OFFERED", student_message_id: 51, entry_id: 9 };
    api.conversation.mockResolvedValue(saved);
    renderPage();
    expect(await screen.findByText(/Saved to My Diary/)).toBeTruthy();
    expect(screen.queryByText("Add to My Diary")).toBeNull();
  });
});

describe("reply formatting", () => {
  it("renders bullet lines after a lead-in line as a list, and never as HTML", async () => {
    api.conversations.mockResolvedValue([{ id: 3, title: "t", created_at: NOW, updated_at: NOW }]);
    api.conversation.mockResolvedValue({
      ...empty(3),
      messages: [{ id: 1, role: "ASSISTANT", content: "For example:\n- Build a **tiny** robot\n- Try <b>coding</b>\n\nWhat do you think?", created_at: NOW }],
    });
    const { container } = renderPage();
    expect(await screen.findByText("What do you think?")).toBeTruthy();
    const chat = container.querySelector("section")!; // the conversation panel
    expect(chat.querySelectorAll("li").length).toBe(2);
    expect(chat.querySelector("strong")?.textContent).toBe("tiny");
    expect(chat.querySelector("b")).toBeNull(); // model text is never rendered as HTML
    expect(chat.textContent).toContain("Try <b>coding</b>");
  });
});

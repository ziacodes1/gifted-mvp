import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Spark, Today } from "../../types/today";

vi.mock("../../api/today", () => ({ todayApi: { get: vi.fn(), act: vi.fn(), markSeen: vi.fn() } }));
vi.mock("../../api/ai", () => ({ aiApi: { profileSynthesis: vi.fn() } }));
vi.mock("../../api/companion", () => ({
  companionApi: { overview: vi.fn(), conversations: vi.fn(), create: vi.fn(), conversation: vi.fn(), send: vi.fn(), dismissDiaryOffer: vi.fn() },
}));
vi.mock("../../api/diary", () => ({
  diaryApi: { overview: vi.fn(), list: vi.fn(), create: vi.fn(), entry: vi.fn(), companionDraft: vi.fn() },
}));
vi.mock("../../api/engagement", () => ({ engagementApi: { overview: vi.fn(), redeem: vi.fn() } }));
vi.mock("../../api/assessments", () => ({ assessmentsApi: { list: vi.fn() } }));
vi.mock("../../api/passport", () => ({ passportApi: { mine: vi.fn() } }));
vi.mock("../../api/ecosystem", () => ({ ecosystemApi: { forYou: vi.fn().mockRejectedValue(new Error("not under test")) } }));
vi.mock("../auth/AuthContext", () => ({ useAuth: () => ({ user: { full_name: "Ada Lovelace", email: "a@t.dev", role: "STUDENT" } }) }));

import { aiApi } from "../../api/ai";
import { companionApi } from "../../api/companion";
import { diaryApi } from "../../api/diary";
import { engagementApi } from "../../api/engagement";
import { assessmentsApi } from "../../api/assessments";
import { passportApi } from "../../api/passport";
import { todayApi } from "../../api/today";
import i18n, { setLanguage } from "../../i18n";
import { CompanionPage } from "../../pages/student/CompanionPage";
import { DashboardPage } from "../../pages/student/DashboardPage";
import { DiaryEntryRoute } from "../../pages/student/DiaryEntryPage";
import { NudgeBell } from "./NudgeBell";
import { TodaySpark } from "./TodaySpark";

const api = vi.mocked(todayApi);

const spark = (over: Partial<Spark>): Spark => ({
  key: "reflect_no_fail",
  type: "REFLECTION",
  status: "NEW",
  route: null,
  target: null,
  actions: ["diary", "companion"],
  fact_index: null,
  points: 0,
  ...over,
});

const today = (over: Partial<Today> = {}): Today => ({
  day: "2026-09-26",
  spark: spark({}),
  motivation: "momentum",
  nudges: [],
  unread: 0,
  ...over,
});

function renderAt(node: React.ReactNode, path = "/app") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <I18nextProvider i18n={i18n}>
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/app" element={node} />
            <Route path="/app/companion" element={<CompanionPage />} />
            <Route path="/app/diary/new" element={<DiaryEntryRoute />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </I18nextProvider>,
  );
}

beforeEach(async () => {
  vi.clearAllMocks();
  await setLanguage("en");
  api.get.mockResolvedValue(today());
});
afterEach(cleanup);

describe("Today's Spark", () => {
  it("renders a reflection with motivation and routes to Diary / Companion", async () => {
    renderAt(<TodaySpark />);
    expect((await screen.findByTestId("spark-title")).textContent).toBe("What would you try if you knew you couldn’t fail?");
    expect(screen.getByText("You’re building momentum.")).toBeTruthy();
    expect(screen.getByText("Capture it in my diary").closest("a")?.getAttribute("href")).toBe("/app/diary/new?spark=reflect_no_fail");
    expect(screen.getByText("Explore it with my AI Companion").closest("a")?.getAttribute("href")).toBe("/app/companion?spark=reflect_no_fail");
  });

  it("state-driven sparks route to Mission / Passport / Assessment with their own button text", async () => {
    api.get.mockResolvedValue(today({ spark: spark({ key: "mn_try_mission", type: "MISSION_NUDGE", route: "mission", target: "design-a-better-school-bag", actions: ["go"] }) }));
    renderAt(<TodaySpark />);
    expect((await screen.findByText("Open the mission")).closest("a")?.getAttribute("href")).toBe("/app/missions/design-a-better-school-bag");
    cleanup();
    api.get.mockResolvedValue(today({ spark: spark({ key: "ns_passport_updated", type: "NEXT_STEP", route: "passport", actions: ["go"] }) }));
    renderAt(<TodaySpark />);
    expect((await screen.findByText("View my Passport")).closest("a")?.getAttribute("href")).toBe("/app/passport");
    cleanup();
    api.get.mockResolvedValue(today({ spark: spark({ key: "ns_start_discovery", type: "NEXT_STEP", route: "assessment", actions: ["go"] }) }));
    renderAt(<TodaySpark />);
    expect((await screen.findByText("Start discovering")).closest("a")?.getAttribute("href")).toBe("/app/assessment");
  });

  it("facts come from the curated pool", async () => {
    api.get.mockResolvedValue(today({ spark: spark({ key: "fact_02", type: "FACT", actions: ["companion"], fact_index: 2 }) }));
    renderAt(<TodaySpark />);
    expect((await screen.findByTestId("spark-title")).textContent).toContain("Al-Khwarizmi");
    expect(screen.getByText("Did you know?")).toBeTruthy();
  });

  it("completes a mini challenge once and shows the done state", async () => {
    const challenge = spark({ key: "ch_ask_field", type: "MINI_CHALLENGE", actions: ["complete"], points: 5 });
    api.get.mockResolvedValue(today({ spark: challenge }));
    api.act.mockResolvedValue(today({ spark: { ...challenge, status: "DONE" } }));
    renderAt(<TodaySpark />);
    fireEvent.click(await screen.findByText("I did it"));
    expect(await screen.findByText("Done for today — nice work!")).toBeTruthy();
    expect(screen.getByText("+5 points")).toBeTruthy();
    expect(screen.queryByText("I did it")).toBeNull();
    expect(api.act).toHaveBeenCalledWith("ch_ask_field", "complete");
  });

  it("can be set aside for today and restored", async () => {
    api.act.mockResolvedValueOnce(today({ spark: spark({ status: "DISMISSED" }) })).mockResolvedValueOnce(today());
    renderAt(<TodaySpark />);
    fireEvent.click(await screen.findByText("Not today"));
    expect(await screen.findByText(/You set today’s spark aside/)).toBeTruthy();
    fireEvent.click(screen.getByText("Show it again"));
    expect(await screen.findByTestId("spark-title")).toBeTruthy();
  });

  it("switches language (the payload is keys only)", async () => {
    renderAt(<TodaySpark />);
    await screen.findByTestId("spark-title");
    await act(async () => setLanguage("uz"));
    expect(screen.getByTestId("spark-title").textContent).toBe("Muvaffaqiyatsizlikka uchramasligingizni bilsangiz, nimani sinab ko‘rardingiz?");
    await act(async () => setLanguage("ru"));
    expect(screen.getByTestId("spark-title").textContent).toBe("Что бы ты попробовал, если бы знал, что не ошибёшься?");
    expect(api.get).toHaveBeenCalledTimes(1); // language switch needs no new request
  });
});

describe("Spark entry points", () => {
  beforeEach(() => {
    vi.mocked(companionApi.overview).mockResolvedValue({ about: { first_name: "Ada", passport_status: "EMPTY", journey_stage: null, interests: [], values: [], missions_completed: 0, next_exploration: null }, suggested_prompts: [] });
    vi.mocked(companionApi.conversations).mockResolvedValue([]);
    vi.mocked(diaryApi.list).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  });

  it("Companion opens with the prompt prefilled but not sent", async () => {
    renderAt(<div />, "/app/companion?spark=reflect_no_fail");
    const box = (await screen.findByLabelText("Tell me what’s on your mind…")) as HTMLTextAreaElement;
    expect(box.value).toBe("What would I try if I knew I couldn’t fail? Help me think it through.");
    expect(screen.getByText(/ready in the message box/)).toBeTruthy();
    expect(companionApi.send).not.toHaveBeenCalled();
    expect(companionApi.create).not.toHaveBeenCalled();
  });

  it("an unknown spark key is ignored", async () => {
    renderAt(<div />, "/app/companion?spark=<script>");
    const box = (await screen.findByLabelText("Tell me what’s on your mind…")) as HTMLTextAreaElement;
    expect(box.value).toBe("");
  });

  it("Diary opens with a writing suggestion; nothing is created", async () => {
    renderAt(<div />, "/app/diary/new?spark=reflect_proud");
    expect(await screen.findByText(/Writing idea from Today’s Spark/)).toBeTruthy();
    const body = screen.getByLabelText("Dear diary…") as HTMLTextAreaElement;
    expect(body.value).toBe("");
    expect(body.placeholder).toBe("What’s one small thing you’re proud of from this week?");
    expect(diaryApi.create).not.toHaveBeenCalled();
  });
});

describe("Updates bell", () => {
  it("shows unread in-app nudges and marks them seen on open", async () => {
    api.get.mockResolvedValue(
      today({
        unread: 2,
        nudges: [
          { kind: "badge", params: { badge: "curious_learner" }, to: "/app/rewards", at: "2026-09-26T08:00:00Z", unread: true },
          { kind: "diary_milestone", params: { count: 5 }, to: "/app/diary", at: "2026-09-25T08:00:00Z", unread: true },
        ],
      }),
    );
    renderAt(<NudgeBell />);
    expect((await screen.findByTestId("nudge-count")).textContent).toBe("2");
    fireEvent.click(screen.getByLabelText("Open updates"));
    expect(screen.getByText("New badge unlocked: Curious Learner")).toBeTruthy();
    expect(screen.getByText("Your diary reached 5 pages")).toBeTruthy();
    expect(api.markSeen).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.queryByTestId("nudge-count")).toBeNull());
  });
});

describe("Student Home", () => {
  it("shows Today's Spark and makes no AI or Companion request", async () => {
    vi.mocked(assessmentsApi.list).mockResolvedValue([]);
    vi.mocked(passportApi.mine).mockResolvedValue({ status: "EMPTY", evidence_summary: { missions: 0 } } as never);
    vi.mocked(diaryApi.overview).mockResolvedValue({ pages_filled: 0, page_target: 100, photo_count: 0, last_entry_at: null, recent_entries: [], book_pages: [], mood_week: [], pending_moment: null });
    vi.mocked(engagementApi.overview).mockRejectedValue(new Error("not needed"));
    renderAt(<DashboardPage />);
    expect(await screen.findByTestId("today-spark")).toBeTruthy();
    expect(aiApi.profileSynthesis).not.toHaveBeenCalled();
    expect(companionApi.send).not.toHaveBeenCalled();
    expect(api.get).toHaveBeenCalledTimes(1);
  });
});

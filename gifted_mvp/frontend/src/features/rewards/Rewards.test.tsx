import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { AxiosError, type AxiosResponse } from "axios";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Badge, EngagementOverview, Reward } from "../../types/engagement";

vi.mock("../../api/engagement", () => ({ engagementApi: { overview: vi.fn(), redeem: vi.fn() } }));

import { engagementApi } from "../../api/engagement";
import i18n, { setLanguage } from "../../i18n";
import { RewardsPage } from "../../pages/student/RewardsPage";
import { EngagementHomeCard } from "./EngagementHomeCard";

const api = vi.mocked(engagementApi);
const WEEK = ["2026-09-21", "2026-09-22", "2026-09-23", "2026-09-24", "2026-09-25", "2026-09-26", "2026-09-27"];

const badge = (key: string, unlocked: boolean, available = true, progress: Badge["progress"] = null): Badge => ({
  key,
  icon: "leaf",
  tone: "green",
  available,
  unlocked,
  unlocked_at: unlocked ? "2026-09-24T10:00:00Z" : null,
  progress,
});

const reward = (over: Partial<Reward>): Reward => ({
  key: "sticker-pack",
  title: "Gifted Sticker Pack",
  description: "Stickers.",
  points_required: 50,
  reward_type: "PHYSICAL",
  image_key: "sticker_pack",
  stock_left: null,
  redeemed: false,
  points_missing: 0,
  can_redeem: true,
  ...over,
});

function overview(over: Partial<EngagementOverview> = {}): EngagementOverview {
  return {
    today: "2026-09-26",
    points: { total_earned: 135, available: 135, spent: 0, this_week: 125 },
    streak: {
      current: 4,
      longest: 6,
      active_today: true,
      week: WEEK.map((date, i) => ({ date, active: [2, 3, 4, 5].includes(i), future: i > 5 })),
      active_days_this_week: 4,
      bonus_days: 7,
      bonus_points: 30,
      had_streak_before: false,
    },
    badges: [
      badge("curious_learner", true),
      badge("diary_champion", false, true, { current: 3, target: 10 }),
      badge("opportunity_seeker", false, false),
    ],
    leaderboard: {
      week_start: WEEK[0],
      top: Array.from({ length: 10 }, (_, i) => ({ rank: i + 1, display_name: `Peer${i} K.`, weekly_points: 300 - i * 10, is_me: false })),
      me: { rank: 14, display_name: "Demo S.", weekly_points: 125, is_me: true },
      active_learners: 20,
    },
    standing: { kind: "keep_going", percent: null },
    rewards: [reward({}), reward({ key: "notebook", title: "Gifted Notebook", points_required: 150, image_key: "notebook", can_redeem: false, points_missing: 15 })],
    redemptions: [],
    recent_activity: [{ type: "MISSION_COMPLETED", points: 60, date: "2026-09-25" }],
    ...over,
  };
}

function renderPage(node = <RewardsPage />) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <I18nextProvider i18n={i18n}>
      <QueryClientProvider client={client}>
        <MemoryRouter>{node}</MemoryRouter>
      </QueryClientProvider>
    </I18nextProvider>,
  );
}

beforeEach(async () => {
  vi.clearAllMocks();
  await setLanguage("en");
  api.overview.mockResolvedValue(overview());
});
afterEach(cleanup);

describe("Streak & Rewards page", () => {
  it("renders real streak, weekly progress, points and activity", async () => {
    renderPage();
    expect((await screen.findByTestId("streak-count")).textContent).toBe("4-day streak");
    expect(screen.getByTestId("weekly-count").textContent).toBe("4/7");
    expect(screen.getByText("Best streak: 6 days")).toBeTruthy();
    expect(screen.getByText("Reach a 7-day streak for +30 bonus points.")).toBeTruthy();
    expect(screen.getByText("Points available").nextSibling?.textContent).toContain("135");
    expect(screen.getByText("Mission completed")).toBeTruthy();
    expect(screen.getByText(/Chatting with the AI Companion, opening pages/)).toBeTruthy();
  });

  it("never shames a missed day", async () => {
    api.overview.mockResolvedValue(overview({ streak: { ...overview().streak, current: 0, active_today: false, had_streak_before: true } }));
    renderPage();
    expect((await screen.findByTestId("streak-count")).textContent).toBe("0-day streak");
    expect(screen.getByText(/Welcome back! Your best streak of 6 days is saved/)).toBeTruthy();
  });

  it("shows locked/unlocked badges honestly", async () => {
    renderPage();
    expect((await screen.findByTestId("badge-curious_learner")).dataset.unlocked).toBe("true");
    expect(screen.getByTestId("badge-diary_champion").dataset.unlocked).toBe("false");
    expect(within(screen.getByTestId("badge-diary_champion")).getByText("3/10")).toBeTruthy();
    expect(within(screen.getByTestId("badge-opportunity_seeker")).getByText("Coming soon")).toBeTruthy();
    expect(screen.getByText("1 of 3 unlocked")).toBeTruthy();
  });

  it("leaderboard shows the top rows and my position outside the top 10, with safe names only", async () => {
    renderPage();
    const board = await screen.findByTestId("leaderboard");
    expect(within(board).getAllByRole("listitem")).toHaveLength(5);
    fireEvent.click(screen.getByText("See top 10"));
    expect(within(screen.getByTestId("leaderboard")).getAllByRole("listitem")).toHaveLength(10);
    expect(screen.getByText("Your position")).toBeTruthy();
    expect(screen.getByText("Demo S.")).toBeTruthy();
    expect(screen.getByTestId("standing").textContent).toContain("You’re building momentum this week.");
  });

  it("top-percent card only claims a percentage the backend calculated", async () => {
    api.overview.mockResolvedValue(overview({ standing: { kind: "top_percent", percent: 10 } }));
    renderPage();
    expect((await screen.findByTestId("standing")).textContent).toContain("You’re in the top 10%!");
    cleanup();
    api.overview.mockResolvedValue(overview({ standing: { kind: "most_active", percent: null } }));
    renderPage();
    expect((await screen.findByTestId("standing")).textContent).toContain("most active learners");
  });

  it("reward catalog + redemption flow", async () => {
    api.redeem.mockResolvedValue({ reward_key: "sticker-pack", reward_type: "PHYSICAL", status: "RESERVED", points_spent: 50, points: overview().points });
    renderPage();
    const notebook = await screen.findByTestId("reward-notebook");
    expect(within(notebook).getByText("15 more points")).toBeTruthy();
    fireEvent.click(within(screen.getByTestId("reward-sticker-pack")).getByText("Redeem"));
    expect(screen.getByText("Redeem “Gifted Sticker Pack”?")).toBeTruthy();
    expect(api.redeem).not.toHaveBeenCalled();
    fireEvent.click(within(screen.getByRole("dialog")).getByText("Redeem"));
    expect(await screen.findByText("Reward reserved. Fulfilment will be handled by the Gifted team.")).toBeTruthy();
    expect(api.redeem).toHaveBeenCalledWith("sticker-pack");
  });

  it("shows a clear reason when redemption is refused", async () => {
    const err = new AxiosError("bad", "400", undefined, undefined, {
      status: 400,
      data: { error: { detail: "already_redeemed", status: 400 } },
    } as AxiosResponse);
    api.redeem.mockRejectedValue(err);
    renderPage();
    fireEvent.click(within(await screen.findByTestId("reward-sticker-pack")).getByText("Redeem"));
    fireEvent.click(within(screen.getByRole("dialog")).getByText("Redeem"));
    expect(await screen.findByText("You’ve already reserved this reward.")).toBeTruthy();
  });

  it("switches language for UI copy (plurals included)", async () => {
    renderPage();
    await screen.findByTestId("streak-count");
    await act(async () => setLanguage("ru"));
    expect(screen.getByTestId("streak-count").textContent).toBe("4 дня подряд");
    expect(screen.getByText("Любознательный ученик")).toBeTruthy();
    expect(screen.getByText("Нужно ещё 15 баллов")).toBeTruthy();
    await act(async () => setLanguage("uz"));
    expect(screen.getByTestId("streak-count").textContent).toBe("4 kunlik seriya");
    expect(screen.getByText("Qiziquvchan o‘quvchi")).toBeTruthy();
  });
});

describe("Home momentum card", () => {
  it("shows streak, points, badges and top 3 from real data", async () => {
    renderPage(<EngagementHomeCard />);
    expect(await screen.findByText("Your momentum")).toBeTruthy();
    expect(screen.getByText("4-day streak")).toBeTruthy();
    expect(screen.getByText(/points available · 1 badge/)).toBeTruthy();
    expect(screen.getByText("Peer0 K.")).toBeTruthy();
    await waitFor(() => expect(screen.getAllByRole("listitem").length).toBe(3));
  });
});

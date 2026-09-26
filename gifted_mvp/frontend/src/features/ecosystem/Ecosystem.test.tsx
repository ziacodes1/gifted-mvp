import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type {
  CircleCard,
  CommunityOverview,
  CommunityPost,
  Eligibility,
  ForYou,
  Match,
  OpportunityCard,
  OpportunityDetail,
  OpportunityList,
  Organization,
  ResourceCard,
  ResourceDetail,
  ResourceList,
} from "../../types/ecosystem";

vi.mock("../../api/ecosystem", () => ({
  ecosystemApi: {
    resources: vi.fn(),
    resource: vi.fn(),
    resourceAction: vi.fn(),
    path: vi.fn(),
    opportunities: vi.fn(),
    opportunity: vi.fn(),
    opportunityAction: vi.fn(),
    community: vi.fn(),
    join: vi.fn(),
    leave: vi.fn(),
    post: vi.fn(),
    report: vi.fn(),
    forYou: vi.fn(),
  },
}));

import { ecosystemApi } from "../../api/ecosystem";
import en from "../../i18n/locales/en.json";
import ru from "../../i18n/locales/ru.json";
import uz from "../../i18n/locales/uz.json";
import i18n, { setLanguage } from "../../i18n";
import { CommunityPage } from "../../pages/student/CommunityPage";
import { OpportunitiesPage } from "../../pages/student/OpportunitiesPage";
import { OpportunityDetailPage } from "../../pages/student/OpportunityDetailPage";
import { ResourceDetailPage } from "../../pages/student/ResourceDetailPage";
import { ResourcesPage } from "../../pages/student/ResourcesPage";
import { EcosystemHomeCard } from "./ForYouCards";

const api = vi.mocked(ecosystemApi);

const org: Organization = {
  slug: "central-innovation-hub",
  name: "Central Innovation Hub",
  type: "COMMUNITY",
  short_description: "A maker space.",
  website_url: "",
  city: "Tashkent",
  country: "Uzbekistan",
  verified: false,
  is_demo: true,
};
const strong: Match = {
  level: "STRONG_FIT",
  reasons: [
    { code: "interest", signal: "investigative", label: "Science & Investigation" },
    { code: "exposure_gap", signal: "exp_science", label: "Science experiments" },
  ],
};
const explore: Match = { level: "EXPLORE", reasons: [] };
const elig = (over: Partial<Eligibility> = {}): Eligibility => ({
  age: { min: 15, max: 18, status: "CHECK" },
  location: { status: "ANYWHERE", mode: "ONLINE", city: "", country: "" },
  deadline: { status: "OPEN", days_left: 40 },
  open_now: true,
  ...over,
});

const opp = (over: Partial<OpportunityCard> = {}): OpportunityCard => ({
  slug: "young-innovators-research-fellowship",
  title: "Young Innovators Research Fellowship",
  short_description: "An 8-week online program.",
  type: "FELLOWSHIP",
  category: "STEM",
  mode: "ONLINE",
  city: "",
  country: "",
  global_available: true,
  age_min: 15,
  age_max: 18,
  application_deadline: "2026-11-05",
  program_start: "2026-11-25",
  program_end: "2027-01-20",
  cover_key: "microscope",
  organization: org,
  featured: true,
  saved: false,
  state: "NONE",
  match: strong,
  eligibility: elig(),
  ...over,
});

const oppDetail = (over: Partial<OpportunityDetail> = {}): OpportunityDetail => ({
  ...opp(),
  description: "Fellows choose a question.",
  skills: ["Research & inquiry"],
  requirements: ["Ages 15–18"],
  faqs: [{ q: "Does it cost anything?", a: "Free in the demo listing." }],
  application_url: "https://example.org/gifted-demo/young-innovators-research-fellowship",
  application_open_at: null,
  has_signals: true,
  ...over,
});

const res = (over: Partial<ResourceCard> = {}): ResourceCard => ({
  slug: "intro-to-robotics",
  title: "How Robots Sense and Move",
  short_description: "A short visual guide.",
  type: "VIDEO",
  category: "STEM",
  cover_key: "robotics",
  duration_minutes: 15,
  difficulty: "BEGINNER",
  is_external: false,
  organization: org,
  featured: false,
  saved: false,
  status: "NOT_STARTED",
  match: strong,
  ...over,
});

const circle = (over: Partial<CircleCard> = {}): CircleCard => ({
  slug: "science-circle",
  name: "Science Circle",
  description: "Share experiments.",
  category: "STEM",
  cover_key: "science_lab",
  icon_key: "flask",
  member_count: 3,
  joined: false,
  reason: { code: "interest", signal: "investigative", label: "Science & Investigation" },
  ...over,
});

const post = (over: Partial<CommunityPost> = {}): CommunityPost => ({
  id: 7,
  author: null,
  author_name: "Aziza Y.",
  circle: { slug: "science-circle", name: "Science Circle" },
  body: "Bugun birinchi marta model o‘qitdim",
  post_type: "SHARE",
  status: "APPROVED",
  mine: false,
  created_at: new Date(Date.now() - 2 * 3600_000).toISOString(),
  ...over,
});

const community = (over: Partial<CommunityOverview> = {}): CommunityOverview => ({
  has_signals: true,
  suggested: [circle()],
  my_circles: [],
  circles: [circle(), circle({ slug: "design-lab", name: "Design Lab", reason: null })],
  feed: [post(), post({ id: 8, author_name: null, body: "No name post" })],
  events: [
    {
      id: 1,
      title: "Design for a Better Tomorrow",
      description: "A virtual workshop.",
      start_at: "2026-10-02T11:00:00Z",
      end_at: null,
      mode: "ONLINE",
      location: "Online",
      external_url: "",
      circle: { slug: "design-lab", name: "Design Lab" },
      organization: null,
    },
  ],
  ...over,
});

function renderAt(path: string, pattern: string, element: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <I18nextProvider i18n={i18n}>
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path={pattern} element={element} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </I18nextProvider>,
  );
}

beforeEach(async () => {
  vi.clearAllMocks();
  await setLanguage("en");
});
afterEach(cleanup);

describe("Opportunities", () => {
  const list = (over: Partial<OpportunityList> = {}): OpportunityList => ({
    has_signals: true,
    featured: opp(),
    items: [opp(), opp({ slug: "ai-hack", title: "AI Builders Weekend Hackathon", type: "HACKATHON", category: "AI_TECH", mode: "IN_PERSON", city: "Tashkent", country: "Uzbekistan", global_available: false, featured: false, match: { level: "NEW_AREA", reasons: [{ code: "new_area", signal: null, label: "" }] }, eligibility: elig({ deadline: { status: "CLOSING_SOON", days_left: 9 } }) })],
    facets: { countries: ["Uzbekistan"], types: ["FELLOWSHIP", "HACKATHON"] },
    ...over,
  });

  it("lists cards with match labels, never percentages, and filters by category", async () => {
    api.opportunities.mockResolvedValue(list());
    renderAt("/app/opportunities", "/app/opportunities", <OpportunitiesPage />);
    expect(await screen.findByText("AI Builders Weekend Hackathon")).toBeTruthy();
    expect(screen.getByText("Recommended for you")).toBeTruthy();
    expect(screen.getByText("New area to try")).toBeTruthy();
    expect(screen.getByText("Closes in 9 days")).toBeTruthy();
    expect(screen.getByText("Connects with your interest in Science & Investigation")).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/\d+\s?%/);
    fireEvent.click(screen.getByRole("button", { name: "STEM" }));
    await waitFor(() => expect(api.opportunities).toHaveBeenLastCalledWith({ category: "STEM" }));
    fireEvent.click(screen.getByRole("button", { name: "Online" }));
    await waitFor(() => expect(api.opportunities).toHaveBeenLastCalledWith({ mode: "ONLINE" }));
  });

  it("detail records a view, and Apply opens the provider page and records only a link open", async () => {
    api.opportunity.mockResolvedValue(oppDetail());
    api.opportunityAction.mockImplementation(async (_slug, action) =>
      oppDetail({ state: action === "open_link" ? "APPLICATION_LINK_OPENED" : "VIEWED" }),
    );
    renderAt("/app/opportunities/young-innovators-research-fellowship", "/app/opportunities/:slug", <OpportunityDetailPage />);
    const apply = (await screen.findByText("Apply now")).closest("a")!;
    await waitFor(() => expect(api.opportunityAction).toHaveBeenCalledWith("young-innovators-research-fellowship", "view"));
    expect(apply.getAttribute("href")).toBe("https://example.org/gifted-demo/young-innovators-research-fellowship");
    expect(apply.getAttribute("target")).toBe("_blank");
    expect(apply.getAttribute("rel")).toContain("noopener");
    expect(screen.getByText(/Demo listing/)).toBeTruthy();
    expect(screen.getByText("Why this matches you")).toBeTruthy();
    fireEvent.click(apply);
    await waitFor(() => expect(api.opportunityAction).toHaveBeenCalledWith("young-innovators-research-fellowship", "open_link"));
    expect(await screen.findByText(/You opened the application page/)).toBeTruthy();
    expect(document.body.textContent?.toLowerCase()).not.toContain("submitted");
    fireEvent.click(screen.getByRole("tab", { name: "FAQ" }));
    expect(screen.getByText("Does it cost anything?")).toBeTruthy();
  });

  it("without Passport signals shows a suggested exploration instead of a match", async () => {
    api.opportunity.mockResolvedValue(oppDetail({ match: explore, has_signals: false, state: "VIEWED" }));
    renderAt("/app/opportunities/x", "/app/opportunities/:slug", <OpportunityDetailPage />);
    expect(await screen.findByText("Suggested exploration")).toBeTruthy();
    expect(screen.queryByText("Strong fit")).toBeNull();
    expect(api.opportunityAction).not.toHaveBeenCalled(); // already viewed
  });

  it("closed opportunities have no apply link", async () => {
    api.opportunity.mockResolvedValue(oppDetail({ eligibility: elig({ deadline: { status: "CLOSED", days_left: null }, open_now: false }), state: "VIEWED" }));
    renderAt("/app/opportunities/x", "/app/opportunities/:slug", <OpportunityDetailPage />);
    expect(await screen.findByText("Applications aren't open")).toBeTruthy();
    expect(screen.queryByText("Apply now")).toBeNull();
  });
});

describe("Resources", () => {
  const list: ResourceList = {
    has_signals: true,
    featured_path: {
      slug: "create-a-more-sustainable-world",
      title: "Create a More Sustainable World",
      description: "Explore real-world solutions.",
      category: "ENVIRONMENT",
      cover_key: "gardening",
      difficulty: "BEGINNER",
      organization: org,
      resource_count: 5,
      duration_minutes: 195,
      completed_count: 0,
      next_resource: "ocean",
    },
    items: [res(), res({ slug: "plan-your-week", title: "Plan Your Week", type: "ARTICLE", match: explore, saved: true })],
  };

  it("shows the featured path, filters by type and toggles bookmarks", async () => {
    api.resources.mockResolvedValue(list);
    api.resourceAction.mockResolvedValue({} as ResourceDetail);
    renderAt("/app/resources", "/app/resources", <ResourcesPage />);
    expect(await screen.findByText("Create a More Sustainable World")).toBeTruthy();
    expect(screen.getByText("5 resources")).toBeTruthy();
    expect(screen.getByText("Start learning path").closest("a")?.getAttribute("href")).toBe("/app/resources/paths/create-a-more-sustainable-world");
    fireEvent.click(screen.getByRole("button", { name: "Remove Plan Your Week from saved" }));
    await waitFor(() => expect(api.resourceAction).toHaveBeenCalledWith("plan-your-week", "unsave"));
    fireEvent.click(screen.getByRole("tab", { name: /Videos/ }));
    await waitFor(() => expect(api.resources).toHaveBeenLastCalledWith(expect.objectContaining({ type: "VIDEO" })));
  });

  it("detail labels demo content honestly and marks completion", async () => {
    const detail: ResourceDetail = {
      ...res({ type: "ARTICLE" }),
      content: { intro: "Robots sense, decide and act.", points: ["Sensors", "Controllers"], try_this: "Find three machines." },
      external_url: "",
      produces_evidence: true,
      evidence_recorded: false,
      tracks_progress: false,
      paths: [],
      has_signals: true,
    };
    api.resource.mockResolvedValue(detail);
    api.resourceAction.mockResolvedValue({ ...detail, status: "COMPLETED", evidence_recorded: true });
    renderAt("/app/resources/intro-to-robotics", "/app/resources/:slug", <ResourceDetailPage />);
    expect(await screen.findByText(/Gifted-curated demo content/)).toBeTruthy();
    expect(screen.getByText(/Provided by Central Innovation Hub/)).toBeTruthy();
    fireEvent.click(screen.getByText("Mark as completed"));
    await waitFor(() => expect(api.resourceAction).toHaveBeenCalledWith("intro-to-robotics", "complete"));
    expect(await screen.findByText("Added to your Passport as exposure evidence.")).toBeTruthy();
  });
});

describe("Community", () => {
  it("shows real member counts, safe names, and needs a circle before posting", async () => {
    api.community.mockResolvedValue(community());
    api.join.mockResolvedValue(community({ my_circles: [circle({ joined: true, member_count: 4 })] }));
    renderAt("/app/community", "/app/community", <CommunityPage />);
    expect(await screen.findByText("Find your people. Grow together.")).toBeTruthy();
    expect(screen.getAllByText("3 members").length).toBeGreaterThan(0);
    expect(screen.getByText("Aziza Y.")).toBeTruthy();
    expect(screen.getByText("Gifted learner")).toBeTruthy();
    expect(screen.getByText("Join a circle to share a post in it.")).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/likes|comments/i);
    fireEvent.click(screen.getAllByRole("button", { name: "Join" })[0]);
    await waitFor(() => expect(api.join).toHaveBeenCalledWith("science-circle"));
    expect(await screen.findByPlaceholderText(/Share an idea/)).toBeTruthy();
  });

  it("new posts wait for review; reports send a reason", async () => {
    const joined = community({ my_circles: [circle({ joined: true })] });
    api.community.mockResolvedValue(joined);
    api.post.mockResolvedValue({ ...joined, feed: [post({ id: 9, mine: true, author: "you", status: "PENDING", body: "My idea" }), ...joined.feed] });
    api.report.mockResolvedValue();
    renderAt("/app/community", "/app/community", <CommunityPage />);
    fireEvent.change(await screen.findByPlaceholderText(/Share an idea/), { target: { value: "My idea" } });
    fireEvent.click(screen.getByRole("button", { name: "Share" }));
    await waitFor(() => expect(api.post).toHaveBeenCalledWith("science-circle", "My idea", "SHARE"));
    expect(await screen.findByText("Waiting for review")).toBeTruthy();
    expect(screen.getByText(/will appear for others after a quick review/)).toBeTruthy();

    fireEvent.click(screen.getAllByText("Report")[0]);
    fireEvent.change(screen.getByLabelText("Reason"), { target: { value: "SPAM" } });
    fireEvent.click(screen.getByText("Send report"));
    await waitFor(() => expect(api.report).toHaveBeenCalledWith(7, "SPAM"));
    expect(await screen.findByText(/the Gifted team will take a look/)).toBeTruthy();
  });

  it("posts are shown as written in any UI language", async () => {
    await setLanguage("ru");
    api.community.mockResolvedValue(community());
    renderAt("/app/community", "/app/community", <CommunityPage />);
    expect(await screen.findByText("Bugun birinchi marta model o‘qitdim")).toBeTruthy();
    expect(screen.getByText("Найди своих. Растите вместе.")).toBeTruthy();
    expect(screen.getByText("Ученик Gifted")).toBeTruthy();
  });
});

describe("Home integration", () => {
  it("shows one resource, one opportunity and one circle", async () => {
    const data: ForYou = { has_signals: true, resource: res(), opportunity: opp(), circle: circle() };
    api.forYou.mockResolvedValue(data);
    renderAt("/app", "/app", <EcosystemHomeCard />);
    expect(await screen.findByText("Recommended resource")).toBeTruthy();
    expect(screen.getByText("Opportunity for you")).toBeTruthy();
    expect(screen.getByText("Suggested community")).toBeTruthy();
    expect(screen.getByText("How Robots Sense and Move").closest("a")?.getAttribute("href")).toBe("/app/resources/intro-to-robotics");
  });

  it("hides itself when suggestions fail", async () => {
    api.forYou.mockRejectedValue(new Error("offline"));
    const { container } = renderAt("/app", "/app", <EcosystemHomeCard />);
    await waitFor(() => expect(container.textContent).toBe(""));
  });
});

describe("Ecosystem translations", () => {
  const keys = (o: object, pre = ""): string[] =>
    Object.entries(o).flatMap(([k, v]) => (v && typeof v === "object" ? keys(v, `${pre}${k}.`) : [`${pre}${k}`.replace(/_(one|few|many|other)$/, "")]));

  it("EN / UZ / RU have the same eco keys, and nav items exist", () => {
    const set = (d: { eco: object }) => [...new Set(keys(d.eco))].sort();
    expect(set(uz)).toEqual(set(en));
    expect(set(ru)).toEqual(set(en));
    for (const d of [en, uz, ru]) expect(Object.keys(d.nav)).toEqual(expect.arrayContaining(["resources", "opportunities", "community"]));
  });

  it("uses Russian plural forms for member counts", async () => {
    await setLanguage("ru");
    expect(i18n.t("eco.community.members", { count: 1 })).toBe("1 участник");
    expect(i18n.t("eco.community.members", { count: 3 })).toBe("3 участника");
    expect(i18n.t("eco.community.members", { count: 7 })).toBe("7 участников");
  });
});

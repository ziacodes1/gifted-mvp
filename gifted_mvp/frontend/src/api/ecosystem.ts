import { api } from "./client";
import type {
  CommunityOverview,
  ForYou,
  LearningPathSummary,
  OpportunityAction,
  OpportunityDetail,
  OpportunityFilters,
  OpportunityList,
  PostType,
  ReportReason,
  ResourceAction,
  ResourceDetail,
  ResourceList,
} from "../types/ecosystem";

export interface ResourceFilters {
  type?: string;
  category?: string;
  q?: string;
  saved?: boolean;
  sort?: "relevant" | "shortest" | "newest";
}

const clean = (params: object) =>
  Object.fromEntries(
    Object.entries(params)
      .filter(([, v]) => v !== undefined && v !== "" && v !== false)
      .map(([k, v]) => [k, v === true ? "1" : v]),
  );

export const ecosystemApi = {
  async resources(filters: ResourceFilters = {}): Promise<ResourceList> {
    const { data } = await api.get<ResourceList>("/resources/", { params: clean(filters) });
    return data;
  },
  async resource(slug: string): Promise<ResourceDetail> {
    const { data } = await api.get<ResourceDetail>(`/resources/${slug}/`);
    return data;
  },
  async resourceAction(slug: string, action: ResourceAction): Promise<ResourceDetail> {
    const { data } = await api.post<ResourceDetail>(`/resources/${slug}/action/`, { action });
    return data;
  },
  async path(slug: string): Promise<LearningPathSummary> {
    const { data } = await api.get<LearningPathSummary>(`/learning-paths/${slug}/`);
    return data;
  },
  async opportunities(filters: OpportunityFilters = {}): Promise<OpportunityList> {
    const { data } = await api.get<OpportunityList>("/opportunities/", { params: clean(filters) });
    return data;
  },
  async opportunity(slug: string): Promise<OpportunityDetail> {
    const { data } = await api.get<OpportunityDetail>(`/opportunities/${slug}/`);
    return data;
  },
  /** `open_link` records that the provider's page was opened — never that the learner applied. */
  async opportunityAction(slug: string, action: OpportunityAction): Promise<OpportunityDetail> {
    const { data } = await api.post<OpportunityDetail>(`/opportunities/${slug}/action/`, { action });
    return data;
  },
  async community(): Promise<CommunityOverview> {
    const { data } = await api.get<CommunityOverview>("/community/");
    return data;
  },
  async join(slug: string): Promise<CommunityOverview> {
    const { data } = await api.post<CommunityOverview>(`/community/circles/${slug}/`);
    return data;
  },
  async leave(slug: string): Promise<CommunityOverview> {
    const { data } = await api.delete<CommunityOverview>(`/community/circles/${slug}/`);
    return data;
  },
  async post(circle: string, body: string, post_type: PostType): Promise<CommunityOverview> {
    const { data } = await api.post<CommunityOverview>("/community/posts/", { circle, body, post_type });
    return data;
  },
  async report(postId: number, reason: ReportReason): Promise<void> {
    await api.post(`/community/posts/${postId}/report/`, { reason });
  },
  async forYou(): Promise<ForYou> {
    const { data } = await api.get<ForYou>("/ecosystem/for-you/");
    return data;
  },
};

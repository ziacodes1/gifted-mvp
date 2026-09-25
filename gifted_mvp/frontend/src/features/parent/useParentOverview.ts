import { useQuery } from "@tanstack/react-query";
import { parentApi } from "../../api/parent";

/** Children → first connected child's overview → (only if missing) its Parent Insight.
 * The insight POST is idempotent server-side and keyed by evidence version, so
 * refreshes reuse the saved insight instead of calling the model again. */
export function useParentOverview() {
  const children = useQuery({ queryKey: ["parent-children"], queryFn: parentApi.children });
  const child = children.data?.[0];

  const overview = useQuery({
    queryKey: ["parent-overview", child?.id],
    queryFn: () => parentApi.overview(child!.id),
    enabled: !!child,
  });

  const pending = overview.data?.parent_insight_state === "PENDING";
  const insightQuery = useQuery({
    queryKey: ["parent-insight", child?.id, overview.data?.updated_at],
    queryFn: () => parentApi.insight(child!.id),
    enabled: !!child && pending,
    staleTime: Infinity,
    retry: 1,
  });

  return {
    loading: children.isLoading || (!!child && overview.isLoading),
    error: children.isError || overview.isError,
    noChild: children.isSuccess && !child,
    data: overview.data,
    insight: overview.data?.parent_insight ?? insightQuery.data ?? null,
    insightLoading: pending && insightQuery.isLoading,
  };
}

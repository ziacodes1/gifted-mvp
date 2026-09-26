import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ecosystemApi } from "../../api/ecosystem";
import type { Category, OpportunityCard, ResourceCard, ResourceType } from "../../types/ecosystem";
import { ArticleIcon, CapIcon, PlayIcon, WrenchIcon } from "./icons";

export const CATEGORIES: Category[] = [
  "STEM",
  "AI_TECH",
  "ARTS",
  "LEADERSHIP",
  "ENTREPRENEURSHIP",
  "SOCIAL_IMPACT",
  "ENVIRONMENT",
  "LANGUAGES",
  "PERSONAL_DEVELOPMENT",
];

export const TYPE_ICON: Record<ResourceType, (p: { className?: string }) => React.JSX.Element> = {
  ARTICLE: ArticleIcon,
  VIDEO: PlayIcon,
  TOOLKIT: WrenchIcon,
  COURSE: CapIcon,
};

export function useSaveResource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (r: Pick<ResourceCard, "slug" | "saved">) => ecosystemApi.resourceAction(r.slug, r.saved ? "unsave" : "save"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["eco"] }),
  });
}

export function useSaveOpportunity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (o: Pick<OpportunityCard, "slug" | "saved">) => ecosystemApi.opportunityAction(o.slug, o.saved ? "unsave" : "save"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["eco"] }),
  });
}

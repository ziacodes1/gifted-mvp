import type { TFunction } from "i18next";
import type { CommunityPost, Eligibility, MatchReason, OpportunityCard, ResourceType } from "../../types/ecosystem";
import { formatDate } from "../../utils/date";

export const ECO_KEYS = {
  resources: ["eco", "resources"] as const,
  resource: (slug: string) => ["eco", "resource", slug] as const,
  path: (slug: string) => ["eco", "path", slug] as const,
  opportunities: ["eco", "opportunities"] as const,
  opportunity: (slug: string) => ["eco", "opportunity", slug] as const,
  community: ["eco", "community"] as const,
  forYou: ["eco", "for-you"] as const,
};

/** A reason is a code + the learner's own signal label; the sentence is built here, so every
 * "why" on screen maps to one deterministic Passport signal. */
export const reasonText = (t: TFunction, r: MatchReason) => t(`eco.reason.${r.code}`, { label: r.label });

export function durationText(t: TFunction, minutes: number) {
  if (minutes < 60) return t("common.minutes", { count: minutes });
  const hours = Math.round((minutes / 60) * 2) / 2;
  return t("eco.hours", { count: hours });
}

export const resourceCta = (t: TFunction, type: ResourceType, inProgress: boolean) =>
  inProgress ? t("eco.resources.cta.continue") : t(`eco.resources.cta.${type}`);

export function ageText(t: TFunction, min: number | null, max: number | null) {
  if (min && max) return t("eco.opportunities.ages", { min, max });
  if (min) return t("eco.opportunities.agesFrom", { min });
  if (max) return t("eco.opportunities.agesUpTo", { max });
  return t("eco.opportunities.anyAge");
}

export function locationText(t: TFunction, o: Pick<OpportunityCard, "mode" | "city" | "country" | "global_available">) {
  if (o.mode === "ONLINE") {
    return o.global_available ? t("eco.opportunities.onlineGlobal") : t("eco.opportunities.onlineIn", { country: o.country });
  }
  const place = [o.city, o.country].filter(Boolean).join(", ");
  return o.mode === "HYBRID" ? t("eco.opportunities.hybridIn", { place }) : place;
}

export function deadlineText(t: TFunction, e: Eligibility, deadline: string | null, lang: string) {
  const d = e.deadline;
  switch (d.status) {
    case "CLOSED":
      return t("eco.opportunities.deadline.closed");
    case "ROLLING":
      return t("eco.opportunities.deadline.rolling");
    case "NOT_YET_OPEN":
      return t("eco.opportunities.deadline.opens", { date: d.opens ? formatDate(d.opens, lang) : "" });
    case "CLOSING_SOON":
      return d.days_left === 0
        ? t("eco.opportunities.deadline.today")
        : t("eco.opportunities.deadline.closesIn", { count: d.days_left ?? 0 });
    default:
      return t("eco.opportunities.deadline.applyBy", { date: deadline ? formatDate(deadline, lang) : "" });
  }
}

/** "2h ago" style, from our own locale strings (browsers lack Uzbek relative-time data). */
export function timeAgo(t: TFunction, iso: string, now: Date = new Date()) {
  const minutes = Math.max(0, Math.round((now.getTime() - new Date(iso).getTime()) / 60000));
  if (minutes < 60) return minutes < 1 ? t("eco.time.now") : t("eco.time.minutes", { count: minutes });
  const hours = Math.round(minutes / 60);
  if (hours < 24) return t("eco.time.hours", { count: hours });
  return t("eco.time.days", { count: Math.round(hours / 24) });
}

export const authorName = (t: TFunction, p: CommunityPost) =>
  p.mine ? t("eco.community.you") : p.author_name ?? t("eco.community.anonymous");

export const initials = (name: string) =>
  name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0]?.toUpperCase())
    .join("");

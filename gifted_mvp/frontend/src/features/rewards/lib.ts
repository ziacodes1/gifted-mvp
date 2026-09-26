import communityAccess from "../../assets/rewards/reward_community_access.webp";
import eventPass from "../../assets/rewards/reward_event_pass.webp";
import expertCourse from "../../assets/rewards/reward_expert_course.webp";
import mentorSession from "../../assets/rewards/reward_mentor_session.webp";
import notebook from "../../assets/rewards/reward_notebook.webp";
import stickerPack from "../../assets/rewards/reward_sticker_pack.webp";
import waterBottle from "../../assets/rewards/reward_water_bottle.webp";

import type { TFunction } from "i18next";
import type { Streak } from "../../types/engagement";

export const ENGAGEMENT_KEY = ["engagement-overview"] as const;

/** Reward artwork by the backend's image_key (the reward data itself is dynamic). */
export const REWARD_IMAGES: Record<string, string> = {
  sticker_pack: stickerPack,
  notebook,
  water_bottle: waterBottle,
  expert_course: expertCourse,
  event_pass: eventPass,
  community_access: communityAccess,
  mentor_session: mentorSession,
};

/** Deterministic daily pick from a localized pool — no AI call, same message all day. */
export function dailyIndex(day: string, size: number): number {
  let h = 0;
  for (const ch of day) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return size ? h % size : 0;
}

/** Initials for a safe display name ("Aziza Y." → "AY"). */
export function initials(name: string | null): string {
  return (name ?? "")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]!.toUpperCase())
    .join("");
}

/** Encouraging, never shaming: a missed day keeps the best streak and invites a fresh start. */
export function streakMessage(t: TFunction, s: Streak): string {
  if (s.current > 0) return s.active_today ? t("rewards.streak.msgActive") : t("rewards.streak.msgAlive");
  if (s.had_streak_before) return t("rewards.streak.msgWelcomeBack", { count: s.longest });
  return t("rewards.streak.msgStart");
}

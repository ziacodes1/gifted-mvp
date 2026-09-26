import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { engagementApi } from "../../api/engagement";
import { ArrowIcon } from "../passport/icons";
import { BadgeMedallion, FlameIcon, MedalIcon } from "./art";
import { ENGAGEMENT_KEY, initials, streakMessage } from "./lib";

/** Student Home: a compact momentum strip — streak, points/badges, top 3. Growth stays first. */
export function EngagementHomeCard() {
  const { t } = useTranslation();
  const { data, isError } = useQuery({ queryKey: ENGAGEMENT_KEY, queryFn: engagementApi.overview, staleTime: 0 });
  if (isError) return null; // gamification never blocks Home
  if (!data) return <div className="h-36 animate-pulse rounded-2xl bg-white shadow-card" />;
  const unlocked = data.badges.filter((b) => b.unlocked);
  const top3 = data.leaderboard.top.slice(0, 3);

  return (
    <section className="card" aria-label={t("rewards.home.title")}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl">{t("rewards.home.title")}</h2>
        <Link to="/app/rewards" className="inline-flex items-center gap-1.5 text-sm font-medium text-forest-700 hover:underline">
          {t("rewards.home.seeRewards")} <ArrowIcon />
        </Link>
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <Link to="/app/rewards" className="flex items-center gap-3 rounded-2xl bg-gradient-to-br from-[#FFF8EC] to-white p-4 ring-1 ring-gold-400/40 transition hover:shadow-soft">
          <span className="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-[#FDE7CF]">
            <FlameIcon className="h-7 w-7" />
          </span>
          <span className="min-w-0">
            <span className="block text-xs text-sage-600">{t("rewards.home.streak")}</span>
            <span className="block font-serif text-2xl leading-tight text-gold-600">{t("rewards.streak.days", { count: data.streak.current })}</span>
            <span className="line-clamp-2 text-xs text-forest-700/80">{streakMessage(t, data.streak)}</span>
          </span>
        </Link>
        <Link to="/app/rewards" className="flex items-center gap-3 rounded-2xl bg-cream-50 p-4 transition hover:shadow-soft">
          <span className="min-w-0 flex-1">
            <span className="flex items-center gap-1.5 font-serif text-2xl leading-tight text-forest-800">
              <MedalIcon className="h-5 w-5" /> {data.points.available}
            </span>
            <span className="block text-xs text-sage-600">
              {t("rewards.home.available")} · {t("rewards.home.badges", { count: unlocked.length })}
            </span>
          </span>
          <span className="flex -space-x-3">
            {(unlocked.length ? unlocked : data.badges.slice(0, 3)).slice(0, 3).map((b) => (
              <BadgeMedallion key={b.key} icon={b.icon} tone={b.tone} unlocked={b.unlocked} className="h-11 w-11" />
            ))}
          </span>
        </Link>
        <div className="rounded-2xl bg-cream-50 p-4">
          <p className="text-xs text-sage-600">{t("rewards.home.top3")}</p>
          {top3.length === 0 ? (
            <p className="mt-2 text-xs text-sage-600">{t("rewards.leaderboard.empty")}</p>
          ) : (
            <ol className="mt-2 space-y-1.5">
              {top3.map((r, i) => (
                <li key={i} className={`flex items-center gap-2 text-sm ${r.is_me ? "font-medium" : ""}`}>
                  <span className="w-4 text-xs text-sage-600">{r.rank}</span>
                  <span className="grid h-6 w-6 place-items-center rounded-full bg-white text-[10px] font-semibold text-forest-700">{initials(r.display_name) || "G"}</span>
                  <span className="min-w-0 flex-1 truncate text-forest-700">{r.is_me ? t("rewards.leaderboard.you") : r.display_name ?? t("rewards.leaderboard.anonymous")}</span>
                  <span className="text-xs text-sage-600">{r.weekly_points}</span>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </section>
  );
}

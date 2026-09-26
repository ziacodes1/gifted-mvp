import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { engagementApi } from "../../api/engagement";
import { ENGAGEMENT_KEY } from "../../features/rewards/lib";
import {
  ActivityAndRules,
  BadgeGallery,
  LeaderboardCard,
  RewardCatalog,
  RewardsHero,
  StreakCard,
  TopPercentCard,
  WeeklyConsistency,
} from "../../features/rewards/RewardsSections";

/** /app/rewards — streak, weekly consistency, leaderboard, badges and rewards (all real data). */
export function RewardsPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ENGAGEMENT_KEY, queryFn: engagementApi.overview, staleTime: 0 });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl space-y-6" aria-busy>
        <div className="h-72 animate-pulse rounded-3xl bg-white" />
        <div className="grid gap-5 lg:grid-cols-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-64 animate-pulse rounded-3xl bg-white" />
          ))}
        </div>
      </div>
    );
  }
  if (isError || !data) {
    return (
      <div className="mx-auto max-w-3xl card text-center">
        <p className="text-sage-600">{t("rewards.catalog.errors.generic")}</p>
        <button onClick={() => void refetch()} className="btn-ghost mt-3">
          {t("common.retry")}
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <RewardsHero points={data.points} today={data.today} />
      <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-[1.25fr_1fr_0.85fr]">
        <StreakCard streak={data.streak} />
        <WeeklyConsistency streak={data.streak} />
        <div className="md:col-span-2 lg:col-span-1">
          <TopPercentCard standing={data.standing} />
        </div>
      </div>
      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[1.35fr_1fr]">
        <LeaderboardCard board={data.leaderboard} />
        <ActivityAndRules activity={data.recent_activity} />
      </div>
      <BadgeGallery badges={data.badges} />
      <RewardCatalog rewards={data.rewards} available={data.points.available} />
    </div>
  );
}

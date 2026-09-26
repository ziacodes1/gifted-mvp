import { useMutation, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { engagementApi } from "../../api/engagement";
import heroImage from "../../assets/rewards/rewards_hero.webp";
import type { Badge, EngagementOverview, Leaderboard, LeaderRow, Reward, Standing, Streak } from "../../types/engagement";
import { formatDate, formatWeekday } from "../../utils/date";
import { parseDay } from "../diary/format";
import { ArrowIcon, ChartIcon, CheckIcon, InfoDot, LeafIcon, UserIcon } from "./smallIcons";
import { BadgeMedallion, FlameIcon, GiftIcon, MedalIcon, TrophyIcon } from "./art";
import { ENGAGEMENT_KEY, REWARD_IMAGES, dailyIndex, initials, streakMessage } from "./lib";

/* ------------------------------------------------------------------ hero + points */

export function RewardsHero({ points, today }: { points: EngagementOverview["points"]; today: string }) {
  const { t } = useTranslation();
  const pool = t("rewards.motivation.active", { returnObjects: true }) as string[];
  const features = [
    { key: "explore", icon: <LeafIcon className="h-6 w-6" /> },
    { key: "build", icon: <ChartIcon className="h-6 w-6" /> },
    { key: "grow", icon: <UserIcon className="h-6 w-6" /> },
    { key: "earn", icon: <MedalIcon className="h-6 w-6" /> },
  ];
  return (
    <div className="relative overflow-hidden rounded-3xl border border-cream-200/80 shadow-card">
      <img src={heroImage} alt="" className="absolute inset-0 h-full w-full object-cover object-[70%_40%]" />
      <div className="absolute inset-0 bg-gradient-to-r from-cream-50 via-cream-50/90 to-cream-50/0 md:via-cream-50/70" />
      <div className="relative max-w-2xl p-7 md:px-10 md:py-9">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-forest-600">{t("rewards.eyebrow")}</p>
        <h1 className="mt-3 text-4xl leading-[1.08] md:text-5xl">
          {t("rewards.titleA")} <span className="text-gold-600">{t("rewards.titleB")}</span>
        </h1>
        <p className="mt-4 max-w-lg leading-relaxed text-forest-700/85">{t("rewards.intro")}</p>
        <ul className="mt-5 grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:flex sm:flex-wrap">
          {features.map((f) => (
            <li key={f.key} className="flex items-center gap-2.5">
              <span className="text-forest-700">{f.icon}</span>
              <span className="leading-tight">
                <span className="block font-medium text-forest-700">{t(`rewards.features.${f.key}.a`)}</span>
                <span className="text-sage-600">{t(`rewards.features.${f.key}.b`)}</span>
              </span>
            </li>
          ))}
        </ul>
        <PointsSummary points={points} />
        <p className="mt-3 font-hand text-xl text-forest-700">{pool[dailyIndex(today, pool.length)]}</p>
      </div>
    </div>
  );
}

export function PointsSummary({ points }: { points: EngagementOverview["points"] }) {
  const { t } = useTranslation();
  const items = [
    { key: "available", value: points.available, strong: true },
    { key: "earned", value: points.total_earned },
    { key: "week", value: points.this_week },
  ];
  return (
    <dl className="mt-6 flex flex-wrap gap-2.5">
      {items.map((i) => (
        <div
          key={i.key}
          className={`rounded-2xl px-4 py-2.5 ${i.strong ? "bg-forest-700 text-cream-50 shadow-soft" : "border border-cream-200 bg-white/85 text-forest-700"}`}
        >
          <dt className={`text-[11px] uppercase tracking-wider ${i.strong ? "text-cream-50/75" : "text-sage-600"}`}>{t(`rewards.points.${i.key}`)}</dt>
          <dd className="flex items-center gap-1.5 font-serif text-2xl leading-tight">
            {i.strong && <MedalIcon className="h-5 w-5" />}
            {i.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}

/* ------------------------------------------------------------------ streak */

export function StreakCard({ streak }: { streak: Streak }) {
  const { t, i18n } = useTranslation();
  return (
    <section className="flex h-full flex-col rounded-3xl border-2 border-gold-400/60 bg-gradient-to-br from-[#FFF8EC] to-white p-5 shadow-card md:p-6">
      <div className="flex items-start gap-4">
        <span className="grid h-16 w-16 shrink-0 place-items-center rounded-full bg-gradient-to-br from-[#FDE7CF] to-[#F9D3B0]">
          <FlameIcon className="h-9 w-9" />
        </span>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="text-lg">{t("rewards.streak.title")}</h2>
            {streak.current >= 3 && (
              <span className="inline-flex items-center gap-1 rounded-full bg-[#FDEBD8] px-2 py-0.5 text-[11px] font-medium text-[#B4541E]">
                <FlameIcon className="h-3 w-3" /> {t("rewards.streak.onRoll")}
              </span>
            )}
          </div>
          <p className="font-serif text-3xl leading-tight text-gold-600 md:text-[2.1rem]" data-testid="streak-count">
            {t("rewards.streak.days", { count: streak.current })}
          </p>
          <p className="mt-1 text-sm leading-relaxed text-forest-700/85">{streakMessage(t, streak)}</p>
        </div>
      </div>
      <ol className="mt-5 grid grid-cols-7 gap-1.5">
        {streak.week.map((d) => (
          <li key={d.date} className="flex flex-col items-center gap-1">
            <span
              className={`grid h-8 w-8 place-items-center rounded-full text-cream-50 ${
                d.active ? "bg-gradient-to-br from-gold-400 to-gold-600 shadow-soft" : d.future ? "border border-dashed border-sage-200" : "border border-cream-200 bg-white"
              }`}
              aria-label={`${formatWeekday(parseDay(d.date), i18n.resolvedLanguage)}: ${d.active ? "✓" : "–"}`}
            >
              {d.active && <CheckIcon className="h-4 w-4" />}
            </span>
            <span className="text-[11px] text-sage-600">{formatWeekday(parseDay(d.date), i18n.resolvedLanguage)}</span>
          </li>
        ))}
      </ol>
      <div className="mt-auto flex flex-wrap justify-between gap-2 pt-4 text-xs text-sage-600">
        <span>{t("rewards.streak.longest", { count: streak.longest })}</span>
        <span>{t("rewards.streak.bonus", { days: streak.bonus_days, points: streak.bonus_points })}</span>
      </div>
    </section>
  );
}

export function WeeklyConsistency({ streak }: { streak: Streak }) {
  const { t } = useTranslation();
  const n = streak.active_days_this_week;
  const r = 44;
  const c = 2 * Math.PI * r;
  return (
    <section className="flex h-full flex-col rounded-3xl border border-cream-200/60 bg-white p-5 shadow-card md:p-6">
      <div className="flex items-center gap-5">
        <svg viewBox="0 0 100 100" className="h-28 w-28 shrink-0 -rotate-90" role="img" aria-label={`${n}/7`}>
          <circle cx="50" cy="50" r={r} fill="none" stroke="#EFE7D6" strokeWidth="9" />
          <circle cx="50" cy="50" r={r} fill="none" stroke="#1E4636" strokeWidth="9" strokeLinecap="round" strokeDasharray={`${(n / 7) * c} ${c}`} />
        </svg>
        <div>
          <h2 className="flex items-center gap-1.5 text-lg">
            {t("rewards.weekly.title")} <InfoDot title={t("rewards.weekly.info")} />
          </h2>
          <p className="font-serif text-5xl leading-none text-forest-700" data-testid="weekly-count">
            {n}/7
          </p>
          <p className="mt-1 text-sm text-forest-700">{t("rewards.weekly.daysActive")}</p>
        </div>
      </div>
      <div className="mt-auto flex items-start gap-3 rounded-2xl bg-cream-50 px-4 py-3 text-sm leading-snug text-forest-700">
        <LeafIcon className="mt-0.5 h-4 w-4 shrink-0 text-gold-600" />
        <span>{n === 7 ? t("rewards.weekly.full") : t("rewards.weekly.help")}</span>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ leaderboard */

const AVATAR_TONES = ["bg-forest-50 text-forest-700", "bg-gold-50 text-gold-600", "bg-[#EEEAFB] text-[#4F46B8]", "bg-[#FDEBD8] text-[#B4541E]"];

function Avatar({ name, index }: { name: string | null; index: number }) {
  return (
    <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-xs font-semibold ${AVATAR_TONES[index % AVATAR_TONES.length]}`} aria-hidden>
      {initials(name) || "G"}
    </span>
  );
}

function RankMark({ rank }: { rank: number | null }) {
  const medal = rank === 1 ? "bg-gold-500 text-white" : rank === 2 ? "bg-[#C8CDD2] text-forest-800" : rank === 3 ? "bg-[#D08B4F] text-white" : "text-sage-600";
  return <span className={`grid h-7 w-7 shrink-0 place-items-center rounded-full text-xs font-semibold ${medal}`}>{rank ?? "–"}</span>;
}

function Row({ row, index }: { row: LeaderRow; index: number }) {
  const { t } = useTranslation();
  const name = row.display_name ?? t("rewards.leaderboard.anonymous");
  return (
    <li className={`flex items-center gap-3 rounded-2xl px-2.5 py-2 ${row.is_me ? "bg-forest-50 ring-1 ring-forest-700/15" : ""}`}>
      <RankMark rank={row.rank} />
      <Avatar name={row.display_name} index={index} />
      <span className="min-w-0 flex-1 truncate text-sm font-medium text-forest-700">
        {name}
        {row.is_me && <span className="ml-1.5 text-xs font-normal text-sage-600">({t("rewards.leaderboard.you")})</span>}
      </span>
      <span className="inline-flex shrink-0 items-center gap-1 text-xs text-forest-700">
        <FlameIcon className="h-3.5 w-3.5" /> {t("rewards.leaderboard.points", { count: row.weekly_points })}
      </span>
    </li>
  );
}

export function LeaderboardTable({ board, preview = 5 }: { board: Leaderboard; preview?: number }) {
  const { t } = useTranslation();
  const [all, setAll] = useState(false);
  const rows = all ? board.top : board.top.slice(0, preview);
  const meVisible = rows.some((r) => r.is_me);
  return (
    <div>
      {board.top.length === 0 ? (
        <p className="rounded-2xl bg-cream-50 p-4 text-sm text-sage-600">{t("rewards.leaderboard.empty")}</p>
      ) : (
        <ol className="space-y-0.5" data-testid="leaderboard">
          {rows.map((r, i) => (
            <Row key={`${r.rank}-${i}`} row={r} index={i} />
          ))}
        </ol>
      )}
      {!meVisible && (
        <div className="mt-2 border-t border-dashed border-cream-200 pt-2">
          <p className="px-2.5 pb-1 text-[11px] uppercase tracking-wider text-sage-600">{t("rewards.leaderboard.yourPosition")}</p>
          {board.me.rank ? <Row row={board.me} index={9} /> : <p className="px-2.5 text-sm text-sage-600">{t("rewards.leaderboard.notRanked")}</p>}
        </div>
      )}
      {board.top.length > preview && (
        <button onClick={() => setAll((v) => !v)} className="mt-2 px-2.5 text-sm font-medium text-forest-700 hover:underline">
          {all ? t("rewards.leaderboard.showLess") : t("rewards.leaderboard.seeAll")}
        </button>
      )}
    </div>
  );
}

export function LeaderboardCard({ board }: { board: Leaderboard }) {
  const { t } = useTranslation();
  return (
    <section className="rounded-3xl border border-cream-200/60 bg-white p-5 shadow-card md:p-6">
      <h2 className="flex items-center gap-2 text-xl">
        <TrophyIcon className="h-5 w-5 text-gold-600" /> {t("rewards.leaderboard.title")}
      </h2>
      <p className="mb-3 mt-0.5 text-xs text-sage-600">{t("rewards.leaderboard.basis")}</p>
      <LeaderboardTable board={board} />
    </section>
  );
}

export function TopPercentCard({ standing }: { standing: Standing }) {
  const { t } = useTranslation();
  const title = standing.kind === "top_percent" ? t("rewards.standing.top_percent", { percent: standing.percent }) : t(`rewards.standing.${standing.kind}`);
  return (
    <section className="flex h-full flex-col justify-between rounded-3xl border border-cream-200/60 bg-gradient-to-b from-forest-50 to-cream-50 p-5 shadow-card md:p-6" data-testid="standing">
      <div>
        <span className="grid h-11 w-11 place-items-center rounded-full bg-white text-gold-600 shadow-soft">
          <TrophyIcon />
        </span>
        <p className="mt-3 font-serif text-2xl leading-snug text-forest-800">{title}</p>
        {standing.kind !== "not_yet" && <p className="mt-1 text-xs leading-relaxed text-sage-600">{t("rewards.standing.sub")}</p>}
      </div>
      <Link to="/app" className="btn-primary mt-4 gap-2 self-start py-2.5">
        {t("rewards.standing.cta")} <ArrowIcon className="h-3.5 w-3.5" />
      </Link>
    </section>
  );
}

/* ------------------------------------------------------------------ badges */

export function BadgeCard({ badge }: { badge: Badge }) {
  const { t, i18n } = useTranslation();
  const title = t(`rewards.badges.items.${badge.key}.title`);
  const status = badge.unlocked
    ? t("rewards.badges.unlocked", { date: formatDate(badge.unlocked_at!, i18n.resolvedLanguage) })
    : !badge.available
      ? t("rewards.badges.soon")
      : null;
  return (
    <li className="flex flex-col items-center px-1 text-center" data-testid={`badge-${badge.key}`} data-unlocked={badge.unlocked}>
      <BadgeMedallion icon={badge.icon} tone={badge.tone} unlocked={badge.unlocked} className={`h-20 w-20 ${badge.unlocked ? "drop-shadow-[0_6px_10px_rgba(30,70,54,0.25)]" : ""}`} />
      <p className={`mt-2 font-serif text-[15px] leading-tight ${badge.unlocked ? "text-forest-800" : "text-forest-700/60"}`}>{title}</p>
      <p className="mt-1 text-[11px] leading-snug text-sage-600">{t(`rewards.badges.items.${badge.key}.condition`)}</p>
      {badge.progress && !badge.unlocked && badge.progress.target > 1 && (
        <div className="mt-1.5 w-16">
          <div className="h-1 overflow-hidden rounded-full bg-cream-200">
            <div className="h-full rounded-full bg-gold-500" style={{ width: `${(badge.progress.current / badge.progress.target) * 100}%` }} />
          </div>
          <p className="mt-0.5 text-[10px] text-sage-600">
            {badge.progress.current}/{badge.progress.target}
          </p>
        </div>
      )}
      {status && <p className={`mt-1 text-[10px] font-medium uppercase tracking-wider ${badge.unlocked ? "text-gold-600" : "text-sage-600"}`}>{status}</p>}
    </li>
  );
}

export function BadgeGallery({ badges }: { badges: Badge[] }) {
  const { t } = useTranslation();
  const unlocked = badges.filter((b) => b.unlocked).length;
  return (
    <SectionCard
      icon={<MedalIcon className="h-7 w-7" />}
      title={t("rewards.badges.title")}
      subtitle={t("rewards.badges.subtitle")}
      aside={<span className="text-sm font-medium text-forest-700">{t("rewards.badges.count", { unlocked, total: badges.length })}</span>}
    >
      <ul className="grid grid-cols-2 gap-x-2 gap-y-6 sm:grid-cols-3 md:grid-cols-5 xl:grid-cols-9">
        {badges.map((b) => (
          <BadgeCard key={b.key} badge={b} />
        ))}
      </ul>
    </SectionCard>
  );
}

/* ------------------------------------------------------------------ rewards */

export function RewardCard({ reward, onRedeem }: { reward: Reward; onRedeem: (r: Reward) => void }) {
  const { t } = useTranslation();
  return (
    <li className="flex flex-col overflow-hidden rounded-2xl border border-cream-200/80 bg-white shadow-soft" data-testid={`reward-${reward.key}`}>
      <div className="aspect-[4/3] overflow-hidden bg-cream-100">
        {REWARD_IMAGES[reward.image_key] && <img src={REWARD_IMAGES[reward.image_key]} alt="" className="h-full w-full object-cover" />}
      </div>
      <div className="flex flex-1 flex-col p-4">
        <p className="font-serif text-[17px] leading-snug text-forest-800">{reward.title}</p>
        <p className="mt-1 line-clamp-3 text-xs leading-relaxed text-sage-600">{reward.description}</p>
        <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-3">
          <span className="inline-flex items-center gap-1.5 text-sm font-medium text-forest-700">
            <MedalIcon className="h-4 w-4" /> {t("rewards.leaderboard.points", { count: reward.points_required })}
          </span>
          {reward.stock_left !== null && reward.stock_left > 0 && !reward.redeemed && (
            <span className="text-[11px] text-sage-600">{t("rewards.catalog.left", { count: reward.stock_left })}</span>
          )}
        </div>
        {reward.redeemed ? (
          <span className="mt-3 inline-flex items-center justify-center gap-1.5 rounded-full bg-forest-50 py-2 text-xs font-medium text-forest-700">
            <CheckIcon className="h-3.5 w-3.5" /> {t("rewards.catalog.reserved")}
          </span>
        ) : reward.stock_left === 0 ? (
          <span className="mt-3 rounded-full bg-cream-100 py-2 text-center text-xs text-sage-600">{t("rewards.catalog.outOfStock")}</span>
        ) : reward.can_redeem ? (
          <button onClick={() => onRedeem(reward)} className="btn-primary mt-3 py-2 text-xs">
            {t("rewards.catalog.redeem")}
          </button>
        ) : (
          <span className="mt-3 rounded-full border border-dashed border-cream-200 py-2 text-center text-xs text-sage-600">
            {t("rewards.catalog.needMore", { count: reward.points_missing })}
          </span>
        )}
      </div>
    </li>
  );
}

type Dialog = { step: "confirm"; reward: Reward } | { step: "done"; reward: Reward } | { step: "error"; reward: Reward; code: string };

export function RewardCatalog({ rewards, available }: { rewards: Reward[]; available: number }) {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const [dialog, setDialog] = useState<Dialog | null>(null);
  const redeem = useMutation({
    mutationFn: (r: Reward) => engagementApi.redeem(r.key),
    onSuccess: (_res, r) => {
      setDialog({ step: "done", reward: r });
      void qc.invalidateQueries({ queryKey: ENGAGEMENT_KEY });
    },
    onError: (err, r) => {
      const code = isAxiosError(err) ? (err.response?.data as { error?: { detail?: string } })?.error?.detail : undefined;
      setDialog({ step: "error", reward: r, code: typeof code === "string" ? code : "generic" });
      void qc.invalidateQueries({ queryKey: ENGAGEMENT_KEY });
    },
  });

  return (
    <SectionCard
      icon={<GiftIcon className="h-7 w-7" />}
      title={t("rewards.catalog.title")}
      subtitle={t("rewards.catalog.subtitle")}
      aside={
        <span className="inline-flex items-center gap-1.5 rounded-full bg-forest-700 px-3 py-1.5 text-sm font-medium text-cream-50">
          <MedalIcon className="h-4 w-4" /> {t("rewards.points.value", { count: available })}
        </span>
      }
    >
      <ul className="grid grid-cols-1 gap-4 min-[430px]:grid-cols-2 md:grid-cols-3 xl:grid-cols-4">
        {rewards.map((r) => (
          <RewardCard key={r.key} reward={r} onRedeem={(reward) => setDialog({ step: "confirm", reward })} />
        ))}
      </ul>

      {dialog && (
        <div role="dialog" aria-modal="true" aria-label={dialog.reward.title} className="fixed inset-0 z-50 grid place-items-center bg-forest-900/30 px-4">
          <div className="w-full max-w-sm overflow-hidden rounded-3xl bg-white shadow-card">
            <img src={REWARD_IMAGES[dialog.reward.image_key]} alt="" className="aspect-[16/7] w-full object-cover" />
            <div className="p-6">
              {dialog.step === "confirm" && (
                <>
                  <p className="font-serif text-xl text-forest-800">{t("rewards.catalog.confirmTitle", { title: dialog.reward.title })}</p>
                  <p className="mt-2 text-sm leading-relaxed text-sage-600">{t("rewards.catalog.confirmText", { points: dialog.reward.points_required })}</p>
                  <div className="mt-5 flex justify-end gap-2">
                    <button onClick={() => setDialog(null)} className="btn-ghost">
                      {t("rewards.catalog.cancel")}
                    </button>
                    <button onClick={() => redeem.mutate(dialog.reward)} disabled={redeem.isPending} className="btn-primary">
                      {t("rewards.catalog.confirm")}
                    </button>
                  </div>
                </>
              )}
              {dialog.step !== "confirm" && (
                <>
                  <p className="font-serif text-xl text-forest-800">{dialog.reward.title}</p>
                  <p role={dialog.step === "error" ? "alert" : "status"} className="mt-2 text-sm leading-relaxed text-forest-700">
                    {dialog.step === "done" ? t(`rewards.catalog.done.${dialog.reward.reward_type}`) : t(`rewards.catalog.errors.${dialog.code}`, { defaultValue: t("rewards.catalog.errors.generic") })}
                  </p>
                  <div className="mt-5 flex justify-end">
                    <button onClick={() => setDialog(null)} className="btn-primary">
                      {t("rewards.catalog.close")}
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </SectionCard>
  );
}

/* ------------------------------------------------------------------ activity + rules */

export function ActivityAndRules({ activity }: { activity: EngagementOverview["recent_activity"] }) {
  const { t, i18n } = useTranslation();
  const rules = t("rewards.howItWorks.items", { returnObjects: true }) as string[];
  return (
    <div className="grid h-full gap-5">
      <SectionCard icon={<ChartIcon className="h-6 w-6" />} title={t("rewards.activity.title")}>
        {activity.length === 0 ? (
          <p className="text-sm text-sage-600">{t("rewards.activity.empty")}</p>
        ) : (
          <ul className="divide-y divide-cream-200">
            {activity.map((a, i) => (
              <li key={i} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                <span className="min-w-0">
                  <span className="block truncate text-forest-700">{t(`rewards.activity.types.${a.type}`)}</span>
                  <span className="text-xs text-sage-600">{formatDate(parseDay(a.date), i18n.resolvedLanguage)}</span>
                </span>
                <span className={`shrink-0 font-medium ${a.points ? "text-gold-600" : "text-sage-600"}`}>{a.points ? `+${a.points}` : "·"}</span>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
      <SectionCard icon={<LeafIcon className="h-6 w-6" />} title={t("rewards.howItWorks.title")}>
        <ul className="space-y-2 text-sm text-forest-700">
          {rules.map((r) => (
            <li key={r} className="flex gap-2">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-gold-500" /> {r}
            </li>
          ))}
        </ul>
        <p className="mt-4 rounded-2xl bg-cream-50 p-3 text-xs leading-relaxed text-sage-600">{t("rewards.howItWorks.note")}</p>
      </SectionCard>
    </div>
  );
}

function SectionCard({ icon, title, subtitle, aside, children }: { icon: ReactNode; title: string; subtitle?: string; aside?: ReactNode; children: ReactNode }) {
  return (
    <section className="rounded-3xl border border-cream-200/60 bg-white p-5 shadow-card md:p-6">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="text-gold-600">{icon}</span>
          <div>
            <h2 className="text-xl">{title}</h2>
            {subtitle && <p className="mt-0.5 text-sm text-sage-600">{subtitle}</p>}
          </div>
        </div>
        {aside}
      </div>
      {children}
    </section>
  );
}

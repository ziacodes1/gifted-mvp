import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { assessmentsApi } from "../../api/assessments";
import { passportApi } from "../../api/passport";
import missionImage from "../../assets/assessment/interest_product_design_backpack_prototype_girl_workshop.webp";
import returningHero from "../../assets/dashboard/dashboard_returning_hero.webp";
import welcomeHero from "../../assets/dashboard/dashboard_welcome_hero.webp";
import passportBook from "../../assets/passport/gifted_passport_book.webp";
import { useAuth } from "../../features/auth/AuthContext";
import { ArrowIcon, ChartIcon, CheckIcon, ClockIcon, CompassIcon, DocIcon, LeafIcon, SparkIcon } from "../../features/passport/icons";
import { JourneyProgress } from "../../features/passport/PassportSections";
import type { Passport } from "../../types/passport";
import { DiaryHomeCard } from "../../features/diary/DiaryHomeCard";
import { EcosystemHomeCard } from "../../features/ecosystem/ForYouCards";
import { EngagementHomeCard } from "../../features/rewards/EngagementHomeCard";
import { TodaySpark } from "../../features/today/TodaySpark";

// Mission artwork: an existing asset whose scene matches the mission.
const MISSION_IMAGES: Record<string, string> = { "design-a-better-school-bag": missionImage };

function greetingKey() {
  const h = new Date().getHours();
  return h < 12 ? "dashboard.greeting.morning" : h < 18 ? "dashboard.greeting.afternoon" : "dashboard.greeting.evening";
}

/** /app — state-aware: a welcome dashboard before the first completed assessment,
 * a "coming back" dashboard afterwards (per the two dashboard references). */
export function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const assessmentsQuery = useQuery({ queryKey: ["assessments"], queryFn: assessmentsApi.list });
  const passportQuery = useQuery({ queryKey: ["passport"], queryFn: passportApi.mine });

  const session = assessmentsQuery.data?.[0]?.my_latest_session ?? null;
  const status = session?.status ?? "NOT_STARTED";
  const firstName = user?.full_name?.split(" ")[0] || t("dashboard.there");

  if (assessmentsQuery.isLoading || passportQuery.isLoading) return <DashboardSkeleton />;

  const passport = passportQuery.data;
  return status === "COMPLETED" && passport && passport.status !== "EMPTY" ? (
    <ReturningDashboard name={firstName} passport={passport} />
  ) : (
    <WelcomeDashboard name={firstName} status={status} progress={session?.progress ?? 0} passport={passport} />
  );
}

/* ---------------------------------------------------------------- shared bits */

function HeroFrame({ image, position, children }: { image: string; position: string; children: ReactNode }) {
  // Photo on the right with its own left-edge blend; text sits on clean cream, never on the subject.
  return (
    <section className="relative overflow-hidden rounded-3xl border border-cream-200/80 bg-cream-50 shadow-card">
      <div className="absolute inset-y-0 right-0 hidden w-[58%] md:block">
        <img src={image} alt="" className={`h-full w-full object-cover ${position}`} />
        <div className="absolute inset-y-0 -left-px w-2/5 bg-gradient-to-r from-cream-50 from-10% to-transparent" />
      </div>
      <div className="relative p-7 md:p-10">{children}</div>
    </section>
  );
}

function IconBubble({ children, tone = "forest" }: { children: ReactNode; tone?: "forest" | "gold" }) {
  return (
    <span
      className={`grid h-14 w-14 shrink-0 place-items-center rounded-full ${
        tone === "gold" ? "bg-gold-50 text-gold-600" : "bg-forest-50 text-forest-700"
      }`}
    >
      {children}
    </span>
  );
}

function PassportBookVisual({ className = "w-28" }: { className?: string }) {
  const { t } = useTranslation();
  return (
    <img
      src={passportBook}
      alt={t("landing.passport.title")}
      className={`-rotate-3 drop-shadow-[0_16px_20px_rgba(22,51,38,0.28)] ${className}`}
    />
  );
}

/* ---------------------------------------------------------------- state 1: welcome */

function WelcomeDashboard({
  name,
  status,
  progress,
  passport,
}: {
  name: string;
  status: string;
  progress: number;
  passport: Passport | undefined;
}) {
  const { t } = useTranslation();
  const started = status === "IN_PROGRESS";
  const missionsDone = passport?.evidence_summary.missions ?? 0;
  const session = [
    { key: "discover", done: false, to: "/app/assessment" },
    { key: "mission", done: missionsDone > 0, to: "/app/missions" },
    { key: "passport", done: false, to: "/app/passport" },
  ].map((s) => ({ ...s, title: t(`dashboard.session.${s.key}.title`), text: t(`dashboard.session.${s.key}.text`) }));

  return (
    <div className="space-y-6">
      <HeroFrame image={welcomeHero} position="object-[60%_35%]">
        <div className="max-w-[31rem]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-forest-600">{t("dashboard.welcomeEyebrow")}</p>
          <h1 className="mt-4 text-5xl leading-[1.05]">
            {t(greetingKey())}, <span className="text-gold-600">{name}</span>
          </h1>
          <p className="mt-4 text-lg leading-relaxed text-forest-700/85">
            {started ? t("dashboard.welcomeStarted", { progress }) : t("dashboard.welcomeNew")}
          </p>
          <ul className="mt-7 flex flex-wrap gap-x-7 gap-y-3 text-sm">
            {[
              { icon: <LeafIcon className="h-5 w-5" />, key: "discover" },
              { icon: <ChartIcon className="h-5 w-5" />, key: "build" },
              { icon: <DocIcon className="h-5 w-5" />, key: "grow" },
            ].map((f) => (
              <li key={f.key} className="flex items-center gap-2.5">
                <span className="text-forest-700">{f.icon}</span>
                <span className="leading-tight">
                  <span className="block font-medium text-forest-700">{t(`dashboard.features.${f.key}.a`)}</span>
                  <span className="text-sage-600">{t(`dashboard.features.${f.key}.b`)}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      </HeroFrame>

      <div className="grid gap-5 lg:grid-cols-3">
        <div className="card flex flex-col border-2 border-gold-400/70">
          <div className="flex items-start gap-4">
            <IconBubble>
              <LeafIcon className="h-6 w-6" />
            </IconBubble>
            <div>
              <span className="inline-flex items-center gap-1 rounded-full bg-gold-50 px-2.5 py-0.5 text-xs font-medium text-gold-600">
                <SparkIcon className="h-3.5 w-3.5" /> {t("dashboard.recommended")}
              </span>
              <h2 className="mt-2 text-xl leading-snug">{started ? t("dashboard.continueJourney") : t("dashboard.startJourney")}</h2>
              <p className="mt-1 text-sm leading-relaxed text-sage-600">
                {started ? t("dashboard.pickUp") : t("dashboard.beginWith")}
              </p>
            </div>
          </div>
          <Link to="/app/assessment" className="btn-primary mt-6 gap-2 py-3">
            {started ? t("dashboard.continueJourney") : t("dashboard.startJourney")} <ArrowIcon />
          </Link>
          <p className="mt-3 flex items-center gap-2 rounded-xl bg-cream-50 px-3 py-2 text-xs text-forest-700">
            <CompassIcon className="h-4 w-4" /> {t("dashboard.stepOf")}
          </p>
        </div>

        <div className="card flex flex-col">
          <div className="flex items-start gap-4">
            <IconBubble>
              <DocIcon className="h-6 w-6" />
            </IconBubble>
            <div>
              <h2 className="text-xl leading-snug">{t("dashboard.assessmentCard.title")}</h2>
              <p className="mt-1 text-sm leading-relaxed text-sage-600">{t("dashboard.assessmentCard.text")}</p>
            </div>
          </div>
          <Link to="/app/assessment" className="btn-ghost mt-auto gap-2 py-3">
            {started ? t("dashboard.assessmentCard.continue") : t("dashboard.assessmentCard.take")} <ArrowIcon />
          </Link>
          <p className="mt-3 flex items-center gap-2 rounded-xl bg-cream-50 px-3 py-2 text-xs text-forest-700">
            <ClockIcon /> {t("dashboard.assessmentCard.time")}
            {started ? ` · ${t("dashboard.assessmentCard.done", { progress })}` : ""}
          </p>
        </div>

        <div className="card flex flex-col bg-gradient-to-br from-white to-forest-50/50">
          <div className="flex items-center gap-4">
            <PassportBookVisual className="w-20 shrink-0" />
            <div>
              <h2 className="text-xl leading-snug">{t("dashboard.passportCard.title")}</h2>
              <p className="mt-1 text-sm leading-relaxed text-sage-600">{t("dashboard.passportCard.text")}</p>
            </div>
          </div>
          <Link to="/app/passport" className="btn-ghost mt-auto gap-2 py-3">
            {t("dashboard.passportCard.preview")} <ArrowIcon />
          </Link>
          <p className="mt-3 flex items-center gap-2 rounded-xl bg-cream-50 px-3 py-2 text-xs text-forest-700">
            <LeafIcon className="h-4 w-4" /> {t("dashboard.passportCard.grows")}
          </p>
        </div>
      </div>

      <TodaySpark />

      <SessionToday items={session} />

      <EcosystemHomeCard />

      <DiaryHomeCard />

      <EngagementHomeCard />
    </div>
  );
}

function SessionToday({ items }: { items: { key: string; title: string; text: string; done: boolean; to: string }[] }) {
  const { t } = useTranslation();
  const done = items.filter((i) => i.done).length;
  return (
    <section className="card">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <IconBubble tone="gold">
            <CompassIcon className="h-6 w-6" />
          </IconBubble>
          <div>
            <h2 className="text-xl">{t("dashboard.session.title")}</h2>
            <p className="text-sm text-sage-600">{t("dashboard.session.subtitle")}</p>
          </div>
        </div>
        <div className="flex w-full items-center gap-3 text-sm font-medium text-forest-700 sm:w-auto sm:min-w-[16rem]">
          {t("dashboard.session.completed", { done, total: items.length })}
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-cream-200">
            <div className="h-full rounded-full bg-gold-500" style={{ width: `${(done / items.length) * 100}%` }} />
          </div>
        </div>
      </div>
      <ol className="mt-5 grid gap-3 md:grid-cols-3">
        {items.map((item, i) => (
          <li key={item.key}>
            <Link
              to={item.to}
              className="flex h-full items-center gap-4 rounded-2xl border border-cream-200 px-4 py-3.5 transition hover:border-forest-600/30 hover:bg-cream-50"
            >
              <span
                className={`grid h-10 w-10 shrink-0 place-items-center rounded-full text-sm font-semibold ${
                  item.done ? "bg-forest-700 text-cream-50" : i === 0 ? "bg-gold-500 text-forest-900" : "bg-cream-100 text-forest-700"
                }`}
              >
                {item.done ? <CheckIcon /> : i + 1}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block font-medium text-forest-700">{item.title}</span>
                <span className="block text-sm text-sage-600">{item.text}</span>
              </span>
              <ArrowIcon className="h-4 w-4 shrink-0 text-sage-600" />
            </Link>
          </li>
        ))}
      </ol>
    </section>
  );
}

/* ---------------------------------------------------------------- state 2: returning */

function ReturningDashboard({ name, passport }: { name: string; passport: Passport }) {
  const { t } = useTranslation();
  const stagesDone = passport.journey.filter((s) => s.done).length;
  const stage = [...passport.journey].reverse().find((s) => s.done)?.label ?? t("dashboard.discoverStage");
  const missions = passport.evidence_summary.missions;
  const mission = passport.recommended_mission;
  const missionDone = mission?.my_attempt?.status === "COMPLETED";
  const missionInProgress = mission?.my_attempt?.status === "IN_PROGRESS";
  const aptitude = passport.other_signals.filter((s) => s.category === "APTITUDE");
  const exposure = passport.other_signals.filter((s) => s.category === "EXPOSURE");

  const stats = [
    { key: "interests", icon: <LeafIcon className="h-6 w-6" />, value: passport.signals.length, unit: t("dashboard.stats.interests.unit", { count: passport.signals.length }), tone: "forest" as const },
    // Puzzles taken, never "right/wrong" counts: 1–2 items are early evidence, not a score.
    { key: "reasoning", icon: <SparkIcon className="h-6 w-6" />, value: aptitude.length, unit: t("dashboard.stats.reasoning.unit", { count: aptitude.length }), tone: "gold" as const },
    { key: "experience", icon: <CompassIcon className="h-6 w-6" />, value: exposure.filter((s) => s.evidence_count > 0).length, unit: t("dashboard.stats.experience.unit", { total: exposure.length || 5 }), tone: "forest" as const },
    { key: "explorations", icon: <ChartIcon className="h-6 w-6" />, value: missions, unit: t("dashboard.stats.explorations.unit", { count: missions }), tone: "gold" as const },
  ];

  return (
    <div className="space-y-6">
      <HeroFrame image={returningHero} position="object-[78%_40%]">
        <div className="max-w-[30rem]">
          <p className="text-2xl text-forest-700">{t("dashboard.welcomeBack")}</p>
          <h1 className="text-5xl leading-tight">{name}!</h1>
          <p className="mt-3 text-lg leading-relaxed text-forest-700/85">
            {missions > 0 ? t("dashboard.growing") : t("dashboard.profileReady")}
          </p>
          <div className="mt-6">
            <div className="flex items-baseline justify-between text-sm">
              <span className="font-medium text-forest-700">{t("dashboard.journeyProgress")}</span>
              <span className="text-sage-600">{t("dashboard.stagesOf", { done: stagesDone, stage })}</span>
            </div>
            <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-cream-200">
              <div className="h-full rounded-full bg-forest-700" style={{ width: `${(stagesDone / 5) * 100}%` }} />
            </div>
          </div>
        </div>
      </HeroFrame>

      <div className="grid gap-5 lg:grid-cols-[1.35fr_1fr]">
        <NextStepCard mission={mission} missionDone={missionDone} missionInProgress={missionInProgress} />
        <div className="card flex flex-col items-center gap-6 sm:flex-row">
          <PassportBookVisual className="w-32 shrink-0 md:w-36" />
          <div className="min-w-0 flex-1">
            <h2 className="text-2xl">{t("landing.passport.title")}</h2>
            <p className="text-sm text-sage-600">{t("landing.passport.text")}</p>
            <span className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-forest-700 px-3 py-1 text-xs font-medium text-cream-50">
              <span className="h-1.5 w-1.5 rounded-full bg-gold-400" />{" "}
              {passport.status === "GROWING" ? t("passport.status.growing") : t("passport.status.emerging")}
            </span>
            <p className="mt-3 text-sm text-forest-700">
              {missions > 0
                ? t("dashboard.builtFromWithMissions", { responses: passport.evidence_summary.assessment, count: missions })
                : t("dashboard.builtFrom", { responses: passport.evidence_summary.assessment })}
            </p>
            <Link to="/app/passport" className="btn-ghost mt-4 gap-2">
              {missions > 0 ? t("dashboard.viewUpdatedPassport") : t("dashboard.viewPassport")} <ArrowIcon />
            </Link>
          </div>
        </div>
      </div>

      <TodaySpark />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((s) => (
          <Link
            key={s.key}
            to="/app/passport"
            className={`flex items-center gap-4 rounded-2xl border border-cream-200/80 p-5 shadow-soft transition hover:shadow-card ${
              s.tone === "gold" ? "bg-gold-50/60" : "bg-forest-50/50"
            }`}
          >
            <IconBubble tone={s.tone}>{s.icon}</IconBubble>
            <div className="min-w-0">
              <p className="font-serif text-lg text-forest-700">{t(`dashboard.stats.${s.key}.title`)}</p>
              <p className="text-xs text-sage-600">{t(`dashboard.stats.${s.key}.sub`)}</p>
              <p className="mt-1 text-forest-700">
                <span className="font-serif text-2xl">{s.value}</span> <span className="text-sm text-sage-600">{s.unit}</span>
              </p>
            </div>
          </Link>
        ))}
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.35fr_1fr]">
        {mission && (
          <div className="card">
            <h2 className="flex items-center gap-2 text-xl">
              <CompassIcon className="h-5 w-5 text-gold-500" />
              {missionDone
                ? t("dashboard.mission.yourExploration")
                : mission.match === "RECOMMENDED"
                  ? t("dashboard.mission.recommended")
                  : t("dashboard.mission.suggested")}
            </h2>
            <div className="mt-4 flex flex-col gap-5 sm:flex-row">
              {MISSION_IMAGES[mission.slug] && (
                <img src={MISSION_IMAGES[mission.slug]} alt="" className="aspect-[4/3] w-full rounded-2xl object-cover sm:w-44" />
              )}
              <div className="flex min-w-0 flex-1 flex-col">
                <span className="self-start rounded-full bg-gold-50 px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-gold-600">
                  {mission.activity_label}
                </span>
                <p className="mt-2 font-serif text-xl text-forest-700">{mission.title}</p>
                <p className="mt-1 text-sm leading-relaxed text-sage-600">{mission.short_description}</p>
                <div className="mt-auto flex flex-wrap items-center justify-between gap-3 pt-4">
                  <span className="inline-flex items-center gap-1.5 text-sm text-sage-600">
                    <ClockIcon /> {mission.time_label} · {t("missions.beginnerFriendly")}
                  </span>
                  {missionDone ? (
                    <Link
                      to={`/app/missions/${mission.slug}`}
                      className="inline-flex items-center gap-1.5 text-sm font-medium text-forest-700 hover:underline"
                    >
                      <CheckIcon /> {t("dashboard.mission.completedView")}
                    </Link>
                  ) : (
                    <Link to={`/app/missions/${mission.slug}`} className="btn-primary gap-2">
                      {missionInProgress ? t("missions.continueMission") : t("missions.startMission")} <ArrowIcon />
                    </Link>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
        <div className="card flex flex-col">
          <h2 className="flex items-center gap-2 text-xl">
            <SparkIcon className="h-5 w-5 text-gold-500" /> {t("dashboard.profile.title")}
          </h2>
          {passport.headline && <p className="mt-4 font-serif text-lg italic leading-snug text-forest-700">{passport.headline}</p>}
          <p className="mt-2 text-sm text-sage-600">{t("dashboard.profile.text")}</p>
          <Link to="/app/assessment/result" className="btn-ghost mt-auto gap-2 self-start">
            {t("dashboard.profile.cta")} <ArrowIcon />
          </Link>
        </div>
      </div>

      <JourneyProgress title={t("dashboard.yourJourney")} stages={passport.journey} />

      <EcosystemHomeCard />

      <DiaryHomeCard />

      <EngagementHomeCard />
    </div>
  );
}

function NextStepCard({
  mission,
  missionDone,
  missionInProgress,
}: {
  mission: Passport["recommended_mission"];
  missionDone: boolean;
  missionInProgress: boolean;
}) {
  const { t } = useTranslation();
  const next =
    mission && !missionDone
      ? {
          title: missionInProgress ? t("dashboard.next.continueTitle") : t("dashboard.next.firstTitle"),
          text: t("dashboard.next.missionText", { title: mission.title }),
          chip: mission.time_label,
          to: `/app/missions/${mission.slug}`,
          cta: missionInProgress ? t("missions.continueMission") : t("missions.startMission"),
        }
      : {
          title: t("dashboard.next.grewTitle"),
          text: t("dashboard.next.grewText"),
          chip: t("common.minutes", { count: 2 }),
          to: "/app/passport",
          cta: t("dashboard.viewUpdatedPassport"),
        };
  return (
    <Link to={next.to} className="group flex flex-col overflow-hidden rounded-3xl bg-forest-700 p-7 text-cream-50 shadow-card">
      <div className="flex items-start justify-between gap-4">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-400">{t("dashboard.next.eyebrow")}</p>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-cream-50/10 px-3 py-1 text-xs">
          <ClockIcon className="h-3.5 w-3.5" /> {next.chip}
        </span>
      </div>
      <h2 className="mt-3 max-w-md text-3xl leading-tight text-cream-50">{next.title}</h2>
      <p className="mt-3 max-w-md text-sm leading-relaxed text-cream-50/80">{next.text}</p>
      <span className="mt-auto inline-flex items-center gap-3 pt-6 text-sm font-medium text-gold-400">
        <span className="grid h-11 w-11 place-items-center rounded-full bg-gold-500 text-forest-900 transition group-hover:translate-x-0.5">
          <ArrowIcon />
        </span>
        {next.cta}
      </span>
    </Link>
  );
}

function DashboardSkeleton() {
  return (
    <div className="animate-pulse space-y-6" aria-busy="true">
      <div className="h-72 rounded-3xl bg-white" />
      <div className="grid gap-5 lg:grid-cols-3">
        <div className="h-56 rounded-2xl bg-white" />
        <div className="h-56 rounded-2xl bg-white" />
        <div className="h-56 rounded-2xl bg-white" />
      </div>
    </div>
  );
}

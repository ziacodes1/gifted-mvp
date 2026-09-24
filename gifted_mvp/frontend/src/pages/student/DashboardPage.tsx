import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
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

// Mission artwork: an existing asset whose scene matches the mission.
const MISSION_IMAGES: Record<string, string> = { "design-a-better-school-bag": missionImage };

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

/** /app — state-aware: a welcome dashboard before the first completed assessment,
 * a "coming back" dashboard afterwards (per the two dashboard references). */
export function DashboardPage() {
  const { user } = useAuth();
  const assessmentsQuery = useQuery({ queryKey: ["assessments"], queryFn: assessmentsApi.list });
  const passportQuery = useQuery({ queryKey: ["passport"], queryFn: passportApi.mine });

  const session = assessmentsQuery.data?.[0]?.my_latest_session ?? null;
  const status = session?.status ?? "NOT_STARTED";
  const firstName = user?.full_name?.split(" ")[0] || "there";

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
        <div className="absolute inset-y-0 left-0 w-2/5 bg-gradient-to-r from-cream-50 to-transparent" />
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
  return (
    <img
      src={passportBook}
      alt="Gifted Passport"
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
  const started = status === "IN_PROGRESS";
  const missionsDone = passport?.evidence_summary.missions ?? 0;
  const session = [
    { title: "Discover your interests", text: "Complete the Discovery assessment.", done: false, to: "/app/assessment" },
    { title: "Try your first mission", text: "A 5–8 minute hands-on challenge.", done: missionsDone > 0, to: "/app/missions" },
    { title: "Open your Passport", text: "See your first signals come together.", done: false, to: "/app/passport" },
  ];

  return (
    <div className="space-y-6">
      <HeroFrame image={welcomeHero} position="object-[60%_35%]">
        <div className="max-w-[31rem]">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-forest-600">Welcome to Gifted</p>
          <h1 className="mt-4 text-5xl leading-[1.05]">
            {greeting()}, <span className="text-gold-600">{name}</span>
          </h1>
          <p className="mt-4 text-lg leading-relaxed text-forest-700/85">
            {started
              ? `You're ${progress}% through your Discovery assessment — pick up right where you left off.`
              : "Today's a great day to take your first step. This session helps you discover what you enjoy and how you think."}
          </p>
          <ul className="mt-7 flex flex-wrap gap-x-7 gap-y-3 text-sm">
            {[
              { icon: <LeafIcon className="h-5 w-5" />, a: "Discover", b: "your interests" },
              { icon: <ChartIcon className="h-5 w-5" />, a: "Build", b: "real evidence" },
              { icon: <DocIcon className="h-5 w-5" />, a: "Grow", b: "your Passport" },
            ].map((f) => (
              <li key={f.a} className="flex items-center gap-2.5">
                <span className="text-forest-700">{f.icon}</span>
                <span className="leading-tight">
                  <span className="block font-medium text-forest-700">{f.a}</span>
                  <span className="text-sage-600">{f.b}</span>
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
                <SparkIcon className="h-3.5 w-3.5" /> Recommended for you
              </span>
              <h2 className="mt-2 text-xl leading-snug">{started ? "Continue My Journey" : "Start My Journey"}</h2>
              <p className="mt-1 text-sm leading-relaxed text-sage-600">
                {started ? "Pick up where you left off." : "Begin with ten short moments about what you enjoy."}
              </p>
            </div>
          </div>
          <Link to="/app/assessment" className="btn-primary mt-6 gap-2 py-3">
            {started ? "Continue My Journey" : "Start My Journey"} <ArrowIcon />
          </Link>
          <p className="mt-3 flex items-center gap-2 rounded-xl bg-cream-50 px-3 py-2 text-xs text-forest-700">
            <CompassIcon className="h-4 w-4" /> You're on step 1 of 5 · Discover
          </p>
        </div>

        <div className="card flex flex-col">
          <div className="flex items-start gap-4">
            <IconBubble>
              <DocIcon className="h-6 w-6" />
            </IconBubble>
            <div>
              <h2 className="text-xl leading-snug">Discovery Assessment</h2>
              <p className="mt-1 text-sm leading-relaxed text-sage-600">
                Activities, situations, two quick puzzles and what you've tried so far.
              </p>
            </div>
          </div>
          <Link to="/app/assessment" className="btn-ghost mt-auto gap-2 py-3">
            {started ? "Continue Assessment" : "Take Assessment"} <ArrowIcon />
          </Link>
          <p className="mt-3 flex items-center gap-2 rounded-xl bg-cream-50 px-3 py-2 text-xs text-forest-700">
            <ClockIcon /> About 5 minutes{started ? ` · ${progress}% done` : ""}
          </p>
        </div>

        <div className="card flex flex-col bg-gradient-to-br from-white to-forest-50/50">
          <div className="flex items-center gap-4">
            <PassportBookVisual className="w-20 shrink-0" />
            <div>
              <h2 className="text-xl leading-snug">Your Gifted Passport</h2>
              <p className="mt-1 text-sm leading-relaxed text-sage-600">Opens with your first signals after the assessment.</p>
            </div>
          </div>
          <Link to="/app/passport" className="btn-ghost mt-auto gap-2 py-3">
            Preview My Passport <ArrowIcon />
          </Link>
          <p className="mt-3 flex items-center gap-2 rounded-xl bg-cream-50 px-3 py-2 text-xs text-forest-700">
            <LeafIcon className="h-4 w-4" /> Grows with every activity
          </p>
        </div>
      </div>

      <SessionToday items={session} />
    </div>
  );
}

function SessionToday({ items }: { items: { title: string; text: string; done: boolean; to: string }[] }) {
  const done = items.filter((i) => i.done).length;
  return (
    <section className="card">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <IconBubble tone="gold">
            <CompassIcon className="h-6 w-6" />
          </IconBubble>
          <div>
            <h2 className="text-xl">Your Session Today</h2>
            <p className="text-sm text-sage-600">A few steps toward your first Passport.</p>
          </div>
        </div>
        <div className="flex w-full items-center gap-3 text-sm font-medium text-forest-700 sm:w-auto sm:min-w-[16rem]">
          {done} of {items.length} completed
          <div className="h-2 flex-1 overflow-hidden rounded-full bg-cream-200">
            <div className="h-full rounded-full bg-gold-500" style={{ width: `${(done / items.length) * 100}%` }} />
          </div>
        </div>
      </div>
      <ol className="mt-5 grid gap-3 md:grid-cols-3">
        {items.map((item, i) => (
          <li key={item.title}>
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
  const stagesDone = passport.journey.filter((s) => s.done).length;
  const stage = [...passport.journey].reverse().find((s) => s.done)?.label ?? "Discover";
  const missions = passport.evidence_summary.missions;
  const mission = passport.recommended_mission;
  const missionDone = mission?.my_attempt?.status === "COMPLETED";
  const missionInProgress = mission?.my_attempt?.status === "IN_PROGRESS";
  const aptitude = passport.other_signals.filter((s) => s.category === "APTITUDE");
  const exposure = passport.other_signals.filter((s) => s.category === "EXPOSURE");

  const stats = [
    { icon: <LeafIcon className="h-6 w-6" />, title: "Interests", sub: "With evidence", value: passport.signals.length, unit: "interest areas", tone: "forest" as const },
    // Puzzles taken, never "right/wrong" counts: 1–2 items are early evidence, not a score.
    { icon: <SparkIcon className="h-6 w-6" />, title: "Reasoning", sub: "Early evidence only", value: aptitude.length, unit: aptitude.length === 1 ? "quick puzzle" : "quick puzzles", tone: "gold" as const },
    { icon: <CompassIcon className="h-6 w-6" />, title: "Experience", sub: "You've tried", value: exposure.filter((s) => s.evidence_count > 0).length, unit: `of ${exposure.length || 5} areas`, tone: "forest" as const },
    { icon: <ChartIcon className="h-6 w-6" />, title: "Explorations", sub: "Completed", value: missions, unit: missions === 1 ? "mission" : "missions", tone: "gold" as const },
  ];

  return (
    <div className="space-y-6">
      <HeroFrame image={returningHero} position="object-[78%_40%]">
        <div className="max-w-[30rem]">
          <p className="text-2xl text-forest-700">Welcome back,</p>
          <h1 className="text-5xl leading-tight">{name}!</h1>
          <p className="mt-3 text-lg leading-relaxed text-forest-700/85">
            {missions > 0 ? "Your Passport is growing — new evidence has been added." : "Your emerging profile is ready. Continue your journey."}
          </p>
          <div className="mt-6">
            <div className="flex items-baseline justify-between text-sm">
              <span className="font-medium text-forest-700">Journey progress</span>
              <span className="text-sage-600">
                {stagesDone} of 5 · {stage}
              </span>
            </div>
            <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-cream-200">
              <div className="h-full rounded-full bg-forest-700" style={{ width: `${(stagesDone / 5) * 100}%` }} />
            </div>
          </div>
        </div>
      </HeroFrame>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((s) => (
          <Link
            key={s.title}
            to="/app/passport"
            className={`flex items-center gap-4 rounded-2xl border border-cream-200/80 p-5 shadow-soft transition hover:shadow-card ${
              s.tone === "gold" ? "bg-gold-50/60" : "bg-forest-50/50"
            }`}
          >
            <IconBubble tone={s.tone}>{s.icon}</IconBubble>
            <div className="min-w-0">
              <p className="font-serif text-lg text-forest-700">{s.title}</p>
              <p className="text-xs text-sage-600">{s.sub}</p>
              <p className="mt-1 text-forest-700">
                <span className="font-serif text-2xl">{s.value}</span> <span className="text-sm text-sage-600">{s.unit}</span>
              </p>
            </div>
          </Link>
        ))}
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.35fr_1fr]">
        <NextStepCard mission={mission} missionDone={missionDone} missionInProgress={missionInProgress} />
        <div className="card flex flex-col items-center gap-6 sm:flex-row">
          <PassportBookVisual className="w-32 shrink-0 md:w-36" />
          <div className="min-w-0 flex-1">
            <h2 className="text-2xl">Gifted Passport</h2>
            <p className="text-sm text-sage-600">Your journey. Your story. Your evidence.</p>
            <span className="mt-3 inline-flex items-center gap-1.5 rounded-full bg-forest-700 px-3 py-1 text-xs font-medium text-cream-50">
              <span className="h-1.5 w-1.5 rounded-full bg-gold-400" /> {passport.status === "GROWING" ? "Growing Passport" : "Emerging Passport"}
            </span>
            <p className="mt-3 text-sm text-forest-700">
              Built from {passport.evidence_summary.assessment} assessment responses
              {missions > 0 && ` and ${missions} exploration mission${missions === 1 ? "" : "s"}`}.
            </p>
            <Link to="/app/passport" className="btn-ghost mt-4 gap-2">
              {missions > 0 ? "View Updated Passport" : "View My Passport"} <ArrowIcon />
            </Link>
          </div>
        </div>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.35fr_1fr]">
        {mission && (
          <div className="card">
            <h2 className="flex items-center gap-2 text-xl">
              <CompassIcon className="h-5 w-5 text-gold-500" />
              {missionDone ? "Your exploration" : mission.match === "RECOMMENDED" ? "Recommended Next Mission" : "Suggested Mission"}
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
                    <ClockIcon /> {mission.time_label} · Beginner friendly
                  </span>
                  {missionDone ? (
                    <Link
                      to={`/app/missions/${mission.slug}`}
                      className="inline-flex items-center gap-1.5 text-sm font-medium text-forest-700 hover:underline"
                    >
                      <CheckIcon /> Completed · View what you added
                    </Link>
                  ) : (
                    <Link to={`/app/missions/${mission.slug}`} className="btn-primary gap-2">
                      {missionInProgress ? "Continue Mission" : "Start Mission"} <ArrowIcon />
                    </Link>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
        <div className="card flex flex-col">
          <h2 className="flex items-center gap-2 text-xl">
            <SparkIcon className="h-5 w-5 text-gold-500" /> Your emerging profile
          </h2>
          {passport.headline && <p className="mt-4 font-serif text-lg italic leading-snug text-forest-700">{passport.headline}</p>}
          <p className="mt-2 text-sm text-sage-600">
            Your first interests, how you think and what you've tried — from your Discovery assessment.
          </p>
          <Link to="/app/assessment/result" className="btn-ghost mt-auto gap-2 self-start">
            View Emerging Profile <ArrowIcon />
          </Link>
        </div>
      </div>

      <JourneyProgress title="Your journey" stages={passport.journey} />
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
  const next =
    mission && !missionDone
      ? {
          title: missionInProgress ? "Continue your mission" : "Try your first mission",
          text: `${mission.title} — a short hands-on challenge that adds new evidence to your Passport.`,
          chip: mission.time_label,
          to: `/app/missions/${mission.slug}`,
          cta: missionInProgress ? "Continue Mission" : "Start Mission",
        }
      : {
          title: "See how your Passport grew",
          text: "Your mission evidence now sits beside your assessment signals. More missions are coming soon.",
          chip: "2 min",
          to: "/app/passport",
          cta: "View Updated Passport",
        };
  return (
    <Link to={next.to} className="group flex flex-col overflow-hidden rounded-3xl bg-forest-700 p-7 text-cream-50 shadow-card">
      <div className="flex items-start justify-between gap-4">
        <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-400">Your next step</p>
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

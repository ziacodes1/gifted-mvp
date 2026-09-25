import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { passportApi } from "../../api/passport";
import { ChartIcon, DocIcon, LeafIcon, SparkIcon } from "../../features/passport/icons";
import { PassportBook, PassportHero, WaveSurface } from "../../features/passport/PassportHero";
import {
  EmergingStrengthCard,
  EvidenceSummary,
  EvolvingMessage,
  ExplorationEvidence,
  ExplorationGapCard,
  JourneyProgress,
  NextStepCard,
  SectionHeader,
  SignalCard,
  SourceTag,
} from "../../features/passport/PassportSections";
import { SignalGroups } from "../../features/assessment/SignalGroups";
import type { Passport } from "../../types/passport";

/** /app/passport — the learner's evolving, evidence-based Gifted Passport (one API call). */
export function PassportPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["passport"],
    queryFn: passportApi.mine,
  });

  if (isLoading) return <PassportSkeleton />;
  if (isError || !data) {
    return (
      <div className="card mx-auto max-w-lg text-center">
        <p className="text-forest-700">We couldn't open your Passport right now.</p>
        <button className="btn-ghost mt-4" onClick={() => refetch()}>
          Try again
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl">
      <PageIntro firstName={data.status === "EMPTY" ? null : data.learner.first_name} />
      {data.status === "EMPTY" ? <EmptyPassport /> : <EmergingPassport passport={data} />}
    </div>
  );
}

function PageIntro({ firstName }: { firstName: string | null }) {
  return (
    <header className="mb-6">
      <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold-600">Gifted Passport</p>
      <h1 className="mt-2 text-4xl leading-tight md:text-5xl">
        {firstName ? `${firstName}’s Passport` : "Your Gifted Passport"}
      </h1>
      <p className="mt-2 max-w-2xl leading-relaxed text-sage-600">
        A living record of your interests, evidence and growth — built from what you’ve explored so far.
      </p>
    </header>
  );
}

function EmergingPassport({ passport }: { passport: Passport }) {
  const answered = passport.evidence_summary.assessment;
  const hasExplore = passport.exploration_gaps.length + passport.suggested_explorations.length > 0;

  return (
    <div className="space-y-8">
      <PassportHero passport={passport} />

      <div className="grid gap-5 md:grid-cols-[1.35fr_1fr]">
        <JourneyProgress stages={passport.journey} />
        <EvidenceSummary evidence={passport.evidence_summary} sources={passport.evidence_sources} />
      </div>

      <section className="space-y-5">
        <SectionHeader
          icon={<ChartIcon />}
          title="Current signals"
          subtitle="From your assessment answers — the insight below explains them, it never changes them."
          tag={<SourceTag kind="calculated" />}
        />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {passport.signals.map((s) => (
            <SignalCard key={s.key} signal={s} answered={answered} />
          ))}
        </div>
        <SignalGroups signals={passport.other_signals} />
      </section>

      {passport.recent_evidence.length > 0 && (
        <section className="space-y-5">
          <SectionHeader
            icon={<DocIcon />}
            title="Evidence from your explorations"
            subtitle="Recorded from what you did in missions. It sits beside your assessment signals — it doesn't change them."
            tag={<SourceTag kind="recorded" />}
          />
          <ExplorationEvidence items={passport.recent_evidence} dimensions={passport.explored_dimensions} />
        </section>
      )}

      <section className="space-y-5">
        <SectionHeader
          icon={<SparkIcon className="h-5 w-5" />}
          title="What your evidence suggests"
          subtitle="An interpretation of the signals above. It explains them — it never changes them."
          tag={passport.insight_source && <SourceTag kind={passport.insight_source} />}
        />
        {passport.summary && (
          <p className="max-w-3xl leading-relaxed text-forest-700">{passport.summary}</p>
        )}
        {!passport.insight_covers_new_evidence && (
          <p className="max-w-3xl rounded-xl border border-gold-400/30 bg-gold-50 px-4 py-3 text-sm leading-relaxed text-forest-700">
            This interpretation was written from your assessment. Your mission evidence is shown above and will be
            included the next time your interpretation is refreshed.
          </p>
        )}
        <div className={`grid gap-5 ${hasExplore ? "md:grid-cols-2" : ""}`}>
          <div className="card">
            <h3 className="text-lg">Emerging strengths</h3>
            <ul className="mt-4 space-y-4">
              {passport.emerging_strengths.map((s) => (
                <EmergingStrengthCard key={s.title} strength={s} />
              ))}
            </ul>
            {passport.uncertainty_notes.length > 0 && (
              <div className="mt-5 border-t border-cream-200 pt-4">
                <p className="text-xs font-medium uppercase tracking-wider text-sage-600">
                  What the evidence can’t tell yet
                </p>
                <ul className="mt-2 space-y-1.5 text-sm leading-relaxed text-forest-700">
                  {passport.uncertainty_notes.map((n) => (
                    <li key={n}>{n}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
          {hasExplore && (
            <div className="card">
              <h3 className="text-lg">Worth exploring</h3>
              <p className="mt-0.5 text-sm text-sage-600">Open questions your next experiences can answer.</p>
              <ul className="mt-4 space-y-2.5">
                {passport.exploration_gaps.map((t) => (
                  <ExplorationGapCard key={t} text={t} />
                ))}
              </ul>
              {passport.suggested_explorations.length > 0 && (
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <span className="text-xs text-sage-600">Ideas to try:</span>
                  {passport.suggested_explorations.map((e) => (
                    <span key={e} className="rounded-full border border-cream-200 bg-white px-3 py-1 text-xs text-forest-700">
                      {e}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </section>

      {passport.next_step && (
        <NextStepCard step={passport.next_step} source={passport.insight_source} mission={passport.recommended_mission} />
      )}

      <EvolvingMessage message={passport.message} />
    </div>
  );
}

function EmptyPassport() {
  const upcoming = [
    { title: "Current signals", text: "Your interest signals, scored from your own answers." },
    { title: "Emerging strengths", text: "What your evidence suggests so far — never a fixed label." },
    { title: "Next exploration", text: "One concrete thing to try, chosen from your signals." },
  ];
  return (
    <WaveSurface>
      <div className="grid items-center gap-8 p-8 md:grid-cols-[auto_1fr] md:p-12">
        <PassportBook className="mx-auto w-40 -rotate-2 opacity-95 md:w-52" />
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-forest-700/15 bg-white/70 px-3 py-1 text-xs font-medium text-forest-700">
            <span className="h-1.5 w-1.5 rounded-full bg-sage-400" /> Passport not started
          </span>
          <h2 className="mt-4 text-3xl leading-tight">Your Gifted Passport starts with discovery.</h2>
          <p className="mt-3 max-w-xl leading-relaxed text-sage-600">
            Complete the Discovery assessment — about 5 minutes — and your Passport will open with
            your first signals.
          </p>
          <ul className="mt-6 grid gap-3 sm:grid-cols-3">
            {upcoming.map((u) => (
              <li key={u.title} className="rounded-2xl border border-cream-200/80 bg-white/80 p-4">
                <LeafIcon className="h-4 w-4 text-forest-700" />
                <p className="mt-2 text-sm font-medium text-forest-700">{u.title}</p>
                <p className="mt-1 text-xs leading-relaxed text-sage-600">{u.text}</p>
              </li>
            ))}
          </ul>
          <Link to="/app/assessment" className="btn-primary mt-7">
            Start Assessment
          </Link>
        </div>
      </div>
    </WaveSurface>
  );
}

function PassportSkeleton() {
  return (
    <div className="mx-auto max-w-6xl animate-pulse space-y-6" aria-busy="true" aria-label="Opening your Passport">
      <div className="h-4 w-32 rounded bg-cream-200" />
      <div className="h-10 w-72 rounded bg-cream-200" />
      <div className="h-64 rounded-3xl bg-white" />
      <div className="grid gap-5 md:grid-cols-2">
        <div className="h-40 rounded-2xl bg-white" />
        <div className="h-40 rounded-2xl bg-white" />
      </div>
    </div>
  );
}

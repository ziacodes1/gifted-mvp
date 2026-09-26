import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { passportApi } from "../../api/passport";
import { ExploreNext } from "../../features/ecosystem/ForYouCards";
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
  const { t } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["passport"],
    queryFn: passportApi.mine,
  });

  if (isLoading) return <PassportSkeleton />;
  if (isError || !data) {
    return (
      <div className="card mx-auto max-w-lg text-center">
        <p className="text-forest-700">{t("passport.page.error")}</p>
        <button className="btn-ghost mt-4" onClick={() => refetch()}>
          {t("common.tryAgain")}
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
  const { t } = useTranslation();
  return (
    <header className="mb-6">
      <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold-600">{t("landing.passport.title")}</p>
      <h1 className="mt-2 text-4xl leading-tight md:text-5xl">
        {firstName ? t("passport.page.titleName", { name: firstName }) : t("dashboard.passportCard.title")}
      </h1>
      <p className="mt-2 max-w-2xl leading-relaxed text-sage-600">{t("passport.page.intro")}</p>
    </header>
  );
}

function EmergingPassport({ passport }: { passport: Passport }) {
  const { t } = useTranslation();
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
          title={t("passport.page.currentSignals")}
          subtitle={t("passport.page.currentSignalsNote")}
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
            title={t("passport.page.explorationEvidence")}
            subtitle={t("passport.page.explorationEvidenceNote")}
            tag={<SourceTag kind="recorded" />}
          />
          <ExplorationEvidence items={passport.recent_evidence} dimensions={passport.explored_dimensions} />
        </section>
      )}

      <section className="space-y-5">
        <SectionHeader
          icon={<SparkIcon className="h-5 w-5" />}
          title={t("passport.page.suggests")}
          subtitle={t("passport.page.suggestsNote")}
          tag={passport.insight_source && <SourceTag kind={passport.insight_source} />}
        />
        {passport.summary && (
          <p className="max-w-3xl leading-relaxed text-forest-700">{passport.summary}</p>
        )}
        {!passport.insight_covers_new_evidence && (
          <p className="max-w-3xl rounded-xl border border-gold-400/30 bg-gold-50 px-4 py-3 text-sm leading-relaxed text-forest-700">
            {t("passport.page.notCovered")}
          </p>
        )}
        <div className={`grid gap-5 ${hasExplore ? "md:grid-cols-2" : ""}`}>
          <div className="card">
            <h3 className="text-lg">{t("insight.strengths")}</h3>
            <ul className="mt-4 space-y-4">
              {passport.emerging_strengths.map((s) => (
                <EmergingStrengthCard key={s.title} strength={s} />
              ))}
            </ul>
            {passport.uncertainty_notes.length > 0 && (
              <div className="mt-5 border-t border-cream-200 pt-4">
                <p className="text-xs font-medium uppercase tracking-wider text-sage-600">{t("passport.page.cantTell")}</p>
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
              <h3 className="text-lg">{t("passport.page.worthExploring")}</h3>
              <p className="mt-0.5 text-sm text-sage-600">{t("passport.page.worthExploringNote")}</p>
              <ul className="mt-4 space-y-2.5">
                {passport.exploration_gaps.map((gap) => (
                  <ExplorationGapCard key={gap} text={gap} />
                ))}
              </ul>
              {passport.suggested_explorations.length > 0 && (
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <span className="text-xs text-sage-600">{t("passport.page.ideas")}</span>
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

      <ExploreNext mission={passport.recommended_mission} />

      <EvolvingMessage message={passport.message} />
    </div>
  );
}

function EmptyPassport() {
  const { t } = useTranslation();
  const upcoming = ["signals", "strengths", "next"].map((key) => ({
    key,
    title: t(`passport.empty.upcoming.${key}.title`),
    text: t(`passport.empty.upcoming.${key}.text`),
  }));
  return (
    <WaveSurface>
      <div className="grid items-center gap-8 p-8 md:grid-cols-[auto_1fr] md:p-12">
        <PassportBook className="mx-auto w-40 -rotate-2 opacity-95 md:w-52" />
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-forest-700/15 bg-white/70 px-3 py-1 text-xs font-medium text-forest-700">
            <span className="h-1.5 w-1.5 rounded-full bg-sage-400" /> {t("passport.empty.badge")}
          </span>
          <h2 className="mt-4 text-3xl leading-tight">{t("passport.empty.title")}</h2>
          <p className="mt-3 max-w-xl leading-relaxed text-sage-600">{t("passport.empty.text")}</p>
          <ul className="mt-6 grid gap-3 sm:grid-cols-3">
            {upcoming.map((u) => (
              <li key={u.key} className="rounded-2xl border border-cream-200/80 bg-white/80 p-4">
                <LeafIcon className="h-4 w-4 text-forest-700" />
                <p className="mt-2 text-sm font-medium text-forest-700">{u.title}</p>
                <p className="mt-1 text-xs leading-relaxed text-sage-600">{u.text}</p>
              </li>
            ))}
          </ul>
          <Link to="/app/assessment" className="btn-primary mt-7">
            {t("result.empty.cta")}
          </Link>
        </div>
      </div>
    </WaveSurface>
  );
}

function PassportSkeleton() {
  const { t } = useTranslation();
  return (
    <div className="mx-auto max-w-6xl animate-pulse space-y-6" aria-busy="true" aria-label={t("passport.page.opening")}>
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

import { useTranslation } from "react-i18next";
import heroImage from "../../assets/parent/parent_hero_sunrise.webp";
import {
  CurrentPicture,
  DiscoveryNotStarted,
  EvidenceCounts,
  InsightLoadingCard,
  LearnerChips,
  NextExploration,
  ParentInsightSummary,
  PrivacyNote,
  StillUnclear,
  SupportAtHome,
} from "../../features/parent/ParentSections";
import { PhotoHero } from "../../components/PhotoHero";
import { NoChildConnected, ParentPageState } from "../../features/parent/ParentStates";
import { useParentOverview } from "../../features/parent/useParentOverview";
import { JourneyProgress } from "../../features/passport/PassportSections";

/** /parent — summary. The deeper explanation lives on /parent/insights. */
export function ParentDashboardPage() {
  const { t } = useTranslation();
  const { loading, error, noChild, data, insight, insightLoading } = useParentOverview();

  if (loading || error) return <ParentPageState error={error} />;
  if (noChild || !data) return <NoChildConnected />;

  const name = data.learner.first_name;
  return (
    <div className="mx-auto max-w-6xl">
      <PhotoHero image={heroImage} eyebrow={t("parent.dashboard.eyebrow")} title={t("parent.dashboard.title")}>
        <p className="mt-3 max-w-xl leading-relaxed text-forest-700/85">
          {data.has_evidence ? t("parent.dashboard.intro", { name }) : t("parent.dashboard.introEmpty", { name })}
        </p>
        <p className="mt-5 font-serif text-2xl text-forest-700">{data.learner.display_name}</p>
        <LearnerChips data={data} />
      </PhotoHero>

      {!data.has_evidence ? (
        <DiscoveryNotStarted name={name} privacy={data.privacy_note} />
      ) : (
        <div className="mt-6 space-y-5">
          <div className="grid gap-5 lg:grid-cols-[1fr_1.15fr]">
            <CurrentPicture data={data} />
            <JourneyProgress
              title={t("parent.dashboard.theirJourney")}
              stages={data.journey}
              note={data.status === "EMERGING" || data.status === "GROWING" ? t(`parent.dashboard.journeyNote.${data.status}`) : undefined}
            />
          </div>

          <div className="grid gap-5 lg:grid-cols-[1.6fr_1fr]">
            {insight ? <ParentInsightSummary insight={insight} /> : insightLoading ? <InsightLoadingCard /> : <div />}
            <EvidenceCounts evidence={data.evidence!} />
          </div>

          {insight && (
            <div className="grid gap-5 md:grid-cols-2">
              <StillUnclear items={insight.content.what_is_still_unclear} />
              <SupportAtHome items={insight.content.support_at_home} />
            </div>
          )}

          <NextExploration data={data} />
          <PrivacyNote text={data.privacy_note} />
        </div>
      )}
    </div>
  );
}

import heroImage from "../../assets/parent/parent_insights_hero.webp";
import {
  CardTitle,
  ConversationStarter,
  DiscoveryNotStarted,
  InsightBadge,
  InsightLoadingCard,
  LearnerChips,
  NextExploration,
  PrivacyNote,
  SupportAtHome,
} from "../../features/parent/ParentSections";
import { PhotoHero } from "../../components/PhotoHero";
import { NoChildConnected, ParentPageState } from "../../features/parent/ParentStates";
import { SignalGroups } from "../../features/assessment/SignalGroups";
import { useParentOverview } from "../../features/parent/useParentOverview";
import { ChartIcon, CompassIcon, DocIcon, LeafIcon, SparkIcon } from "../../features/passport/icons";
import { SignalStrength } from "../../features/passport/PassportSections";
import { iconForSignal } from "../../utils/signalIcons";

const CONFIDENCE_WORD = { HIGH: "Consistent", MEDIUM: "Developing", LOW: "Early" } as const;

/** /parent/insights — the explanation behind the dashboard summary. */
export function ParentInsightsPage() {
  const { loading, error, noChild, data, insight, insightLoading } = useParentOverview();

  if (loading || error) return <ParentPageState error={error} />;
  if (noChild || !data) return <NoChildConnected />;

  const name = data.learner.first_name;
  const answered = data.evidence?.assessment ?? 0;

  return (
    <div className="mx-auto max-w-6xl">
      <PhotoHero image={heroImage} eyebrow="Parent insights" title={`${name}'s current picture, explained`}>
        <p className="mt-3 max-w-xl leading-relaxed text-forest-700/85">
          What we're seeing, the evidence behind it, what's still uncertain — and how to help without deciding too early.
        </p>
        <LearnerChips data={data} />
      </PhotoHero>

      {!data.has_evidence ? (
        <DiscoveryNotStarted name={name} privacy={data.privacy_note} />
      ) : (
        <div className="mt-8 space-y-8">
          {/* 1. What we're seeing */}
          <section>
            {insight ? (
              <div className="card md:p-8">
                <CardTitle icon={<LeafIcon className="h-4 w-4" />} title="What we're seeing" aside={<InsightBadge source={insight.source} />} />
                <p className="mt-4 max-w-3xl font-serif text-xl leading-snug text-forest-700">{insight.content.summary}</p>
                <div className="mt-6 grid gap-4 md:grid-cols-3">
                  {insight.content.what_we_are_seeing.map((s) => (
                    <div key={s.title} className="rounded-2xl border border-cream-200 bg-cream-50 p-5">
                      <p className="font-medium text-forest-700">{s.title}</p>
                      <p className="mt-1.5 text-sm leading-relaxed text-sage-600">{s.explanation}</p>
                    </div>
                  ))}
                </div>
                <p className="mt-4 text-xs text-sage-600">
                  {insight.source === "AI"
                    ? "AI-assisted: written from the signals and activities below. It explains them — it never scores your child."
                    : "Written from the signals and activities below."}
                </p>
              </div>
            ) : insightLoading ? (
              <InsightLoadingCard />
            ) : null}
          </section>

          {/* 2. Evidence behind it */}
          <section className="grid gap-5 lg:grid-cols-2">
            <div className="card">
              <CardTitle icon={<ChartIcon className="h-4 w-4" />} title="Evidence behind it: signals" />
              <p className="mt-1 text-sm text-sage-600">From {answered} assessment answers.</p>
              <ul className="mt-5 space-y-4">
                {(data.current_signals ?? []).map((s) => (
                  <li key={s.key}>
                    <div className="flex items-baseline justify-between gap-3 text-sm">
                      <span className="font-medium text-forest-700">
                        {iconForSignal(s.key)} {s.label}
                      </span>
                      <span className="text-sage-600">
                        {CONFIDENCE_WORD[s.confidence]} · {s.evidence_count}/{s.opportunity_count || answered}
                      </span>
                    </div>
                    <div className="mt-2">
                      <SignalStrength score={s.score} confidence={s.confidence} />
                    </div>
                  </li>
                ))}
              </ul>
              <p className="mt-5 rounded-xl bg-cream-50 px-4 py-3 text-xs leading-relaxed text-sage-600">
                A score is the share of chances where your child picked that interest. Mission evidence is recorded
                separately and never changes these numbers.
              </p>
            </div>
            <div className="card">
              <CardTitle icon={<DocIcon className="h-4 w-4" />} title="Evidence behind it: activities" />
              {data.recent_activity && data.recent_activity.length > 0 ? (
                <>
                  <ul className="mt-4 space-y-3">
                    {data.recent_activity.map((a) => (
                      <li key={a.id} className="rounded-2xl bg-cream-50 px-4 py-3">
                        <p className="font-medium text-forest-700">{a.title}</p>
                        <p className="text-xs text-sage-600">
                          {a.source_label} ·{" "}
                          {new Date(a.created_at).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}
                        </p>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-5 text-xs font-medium uppercase tracking-wider text-sage-600">Explored so far</p>
                  <ul className="mt-2 divide-y divide-cream-200">
                    {(data.explored_dimensions ?? []).map((d) => (
                      <li key={d.key} className="flex items-center justify-between gap-3 py-2 text-sm">
                        <span className="text-forest-700">{d.label}</span>
                        <span className="text-right text-xs text-sage-600">{d.kinds.join(" · ")}</span>
                      </li>
                    ))}
                  </ul>
                </>
              ) : (
                <p className="mt-4 rounded-xl bg-cream-50 px-4 py-3 text-sm leading-relaxed text-forest-700">
                  No hands-on activities yet — so far the picture comes only from the assessment. A first mission will
                  add evidence from real choices.
                </p>
              )}
            </div>
          </section>

          {data.other_signals && data.other_signals.length > 0 && (
            <section>
              <h2 className="text-xl">Beyond interests</h2>
              <p className="mt-0.5 text-sm text-sage-600">Early reasoning, work style, values and experience — kept separate from interests.</p>
              <div className="mt-4">
                <SignalGroups signals={data.other_signals} voice="they" />
              </div>
            </section>
          )}

          {/* 3. Uncertainty */}
          <section className="card">
            <CardTitle icon={<CompassIcon className="h-4 w-4" />} title="What is still uncertain" />
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              {/* The parent insight already reflects evidence limits; fall back to the Passport's gaps only without it. */}
              {(insight?.content.what_is_still_unclear ?? data.areas_to_explore ?? []).map((t) => (
                <p key={t} className="rounded-xl bg-cream-50 px-4 py-3 text-sm leading-relaxed text-forest-700">
                  {t}
                </p>
              ))}
            </div>
          </section>

          {/* 4. What to try next */}
          <NextExploration data={data} />

          {/* 5. Support + 6. Conversation */}
          {insight && (
            <div className="grid gap-5 lg:grid-cols-[1fr_1.1fr]">
              <SupportAtHome items={insight.content.support_at_home} />
              <ConversationStarter text={insight.content.conversation_starter} caution={insight.content.caution} />
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-3">
            <PrivacyNote text={data.privacy_note} />
            <span className="inline-flex items-center gap-1.5 text-xs text-sage-600">
              <SparkIcon className="h-3.5 w-3.5" /> Updates when {name} adds new evidence.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

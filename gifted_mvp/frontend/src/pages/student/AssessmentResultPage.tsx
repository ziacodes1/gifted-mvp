import { useQuery } from "@tanstack/react-query";
import { Link, useLocation } from "react-router-dom";
import { aiApi } from "../../api/ai";
import { signalsApi } from "../../api/signals";
import { InsightDetails, InsightHero, InsightLoading } from "../../features/assessment/ProfileInsight";
import { SignalGroups } from "../../features/assessment/SignalGroups";
import { SignalRing } from "../../features/assessment/SignalRing";
import { iconForSignal } from "../../utils/signalIcons";
import { confidenceWording } from "../../utils/confidence";
import type { CompleteResult } from "../../types/assessment";

/** /app/assessment/result — "Your Emerging Profile".
 * Prefers the fresh payload from just-completed assessment (router state);
 * falls back to /signals/me/ so the screen also works after a reload.
 * Assessment signal scores render immediately; the AI interpretation is
 * fetched separately (persisted server-side, so refreshes don't re-generate).
 */
export function AssessmentResultPage() {
  const location = useLocation();
  const stateResult = (location.state as { result?: CompleteResult } | null)?.result;

  // Always read stored signals: they carry category + chances for grouping.
  const signalsQuery = useQuery({ queryKey: ["my-signals"], queryFn: signalsApi.mine });
  const allSignals = signalsQuery.data ?? [];
  const signals = allSignals
    .filter((s) => s.category === "INTEREST" && s.evidence_count > 0)
    .sort((a, b) => b.score - a.score);
  const otherSignals = allSignals.filter((s) => s.category !== "INTEREST");
  const topSignals = signals.slice(0, 3);
  const exposureNote =
    stateResult?.exposure_note ??
    "These are early signals from your assessments. Real-world exploration will help confirm and refine them.";

  const loading = signalsQuery.isLoading;

  // POST is idempotent get-or-create on the backend, so a query is safe here.
  const sessionId = stateResult?.session_id;
  const insightQuery = useQuery({
    queryKey: ["profile-insight", sessionId ?? "latest"],
    queryFn: () => aiApi.profileSynthesis(sessionId),
    enabled: signals.length > 0,
    staleTime: Infinity,
    retry: 1,
  });
  const insight = insightQuery.data;

  if (loading) {
    return <div className="grid h-64 place-items-center text-sage-600">Loading your profile…</div>;
  }

  if (signals.length === 0) {
    return (
      <div className="card mx-auto max-w-lg text-center">
        <p className="text-forest-700">No signals yet.</p>
        <p className="mt-2 text-sm text-sage-600">Complete an assessment to see your emerging profile.</p>
        <Link to="/app/assessment" className="btn-primary mt-4 inline-flex">
          Start Assessment
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl">
      <p className="text-xs font-semibold uppercase tracking-widest text-gold-600">
        Your potential in focus
      </p>
      <h1 className="mt-2 text-3xl">Your emerging profile</h1>
      <p className="mt-2 max-w-2xl text-sm leading-relaxed text-sage-600">
        Here's a summary of what we've learned from your assessment so far. This reflects
        early signals, not fixed conclusions — it will keep evolving as you explore.
      </p>

      {insight ? (
        <InsightHero insight={insight} signals={signals} />
      ) : insightQuery.isError ? (
        <div className="card mt-6">
          <p className="text-xs font-medium uppercase tracking-widest text-sage-600">Overall insight</p>
          <p className="mt-2 text-lg leading-relaxed text-forest-700">
            Your current responses show stronger interest in{" "}
            <span className="font-semibold">{topSignals[0]?.label}</span>
            {topSignals[1] && (
              <>
                {" "}
                and <span className="font-semibold">{topSignals[1].label}</span>
              </>
            )}
            . This is an emerging signal, not a fixed label.
          </p>
          <p className="mt-4 rounded-xl bg-forest-50 px-4 py-3 text-sm text-forest-700">
            {exposureNote}
          </p>
        </div>
      ) : (
        <InsightLoading />
      )}

      <div className="mt-8">
        <h2 className="text-lg">Current interests</h2>
        <p className="text-sm text-sage-600">
          Assessment signals from your answers — they stay the same whatever the insight says.
        </p>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {signals.map((s) => (
            <div key={s.key} className="card flex items-start gap-4">
              <SignalRing score={s.score} />
              <div>
                <p className="flex items-center gap-1.5 font-medium text-forest-700">
                  <span>{iconForSignal(s.key)}</span> {s.label}
                </p>
                <p className="mt-1 text-xs text-sage-600">{confidenceWording(s.confidence)}</p>
                <p className="mt-1 text-xs text-sage-600">
                  Picked {s.evidence_count} of {s.opportunity_count} times
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {otherSignals.some((s) => s.evidence_count > 0 || s.category === "EXPOSURE") && (
        <div className="mt-8">
          <h2 className="text-lg">Beyond interests</h2>
          <p className="text-sm text-sage-600">Reasoning, work style, values and experience — kept separate on purpose.</p>
          <div className="mt-4">
            <SignalGroups signals={otherSignals} />
          </div>
        </div>
      )}

      {insight && <InsightDetails insight={insight} />}

      <div className="mt-8 flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="max-w-md text-sm text-sage-600">
          More real-world exploration can help clarify and grow these signals over time.
        </p>
        <Link to="/app/passport" className="btn-primary shrink-0">
          Build My Gifted Passport
        </Link>
      </div>
    </div>
  );
}

import { useQuery } from "@tanstack/react-query";
import { Trans, useTranslation } from "react-i18next";
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
  const { t, i18n } = useTranslation();
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
  // The router-state note was written in the language active at completion; the UI copy follows the current one.
  const exposureNote = t("result.exposureNote");

  const loading = signalsQuery.isLoading;

  // POST is idempotent get-or-create on the backend, so a query is safe here. The language is
  // part of the key: switching to Uzbek fetches (once) the Uzbek insight, switching back reuses English.
  const sessionId = stateResult?.session_id;
  const insightQuery = useQuery({
    queryKey: ["profile-insight", sessionId ?? "latest", i18n.resolvedLanguage],
    queryFn: () => aiApi.profileSynthesis(sessionId),
    enabled: signals.length > 0,
    staleTime: Infinity,
    retry: 1,
  });
  const insight = insightQuery.data;

  if (loading) {
    return <div className="grid h-64 place-items-center text-sage-600">{t("result.loading")}</div>;
  }

  if (signals.length === 0) {
    return (
      <div className="card mx-auto max-w-lg text-center">
        <p className="text-forest-700">{t("result.empty.title")}</p>
        <p className="mt-2 text-sm text-sage-600">{t("result.empty.text")}</p>
        <Link to="/app/assessment" className="btn-primary mt-4 inline-flex">
          {t("result.empty.cta")}
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl">
      <p className="text-xs font-semibold uppercase tracking-widest text-gold-600">{t("result.eyebrow")}</p>
      <h1 className="mt-2 text-3xl">{t("result.title")}</h1>
      <p className="mt-2 max-w-2xl text-sm leading-relaxed text-sage-600">{t("result.intro")}</p>

      {insight ? (
        <InsightHero insight={insight} signals={signals} />
      ) : insightQuery.isError ? (
        <div className="card mt-6">
          <p className="text-xs font-medium uppercase tracking-widest text-sage-600">{t("insight.overall")}</p>
          <p className="mt-2 text-lg leading-relaxed text-forest-700">
            <Trans
              i18nKey={topSignals[1] ? "result.offlineTwo" : "result.offlineOne"}
              values={{ a: topSignals[0]?.label, b: topSignals[1]?.label }}
              components={{ b: <span className="font-semibold" /> }}
            />
          </p>
          <p className="mt-4 rounded-xl bg-forest-50 px-4 py-3 text-sm text-forest-700">
            {exposureNote}
          </p>
        </div>
      ) : (
        <InsightLoading />
      )}

      <div className="mt-8">
        <h2 className="text-lg">{t("result.currentInterests")}</h2>
        <p className="text-sm text-sage-600">{t("result.currentInterestsNote")}</p>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {signals.map((s) => (
            <div key={s.key} className="card flex items-start gap-4">
              <SignalRing score={s.score} />
              <div>
                <p className="flex items-center gap-1.5 font-medium text-forest-700">
                  <span>{iconForSignal(s.key)}</span> {s.label}
                </p>
                <p className="mt-1 text-xs text-sage-600">{confidenceWording(s.confidence, t)}</p>
                <p className="mt-1 text-xs text-sage-600">
                  {t("signals.pickedOf", { picked: s.evidence_count, total: s.opportunity_count })}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {otherSignals.some((s) => s.evidence_count > 0 || s.category === "EXPOSURE") && (
        <div className="mt-8">
          <h2 className="text-lg">{t("result.beyond")}</h2>
          <p className="text-sm text-sage-600">{t("result.beyondNote")}</p>
          <div className="mt-4">
            <SignalGroups signals={otherSignals} />
          </div>
        </div>
      )}

      {insight && <InsightDetails insight={insight} />}

      <div className="mt-8 flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="max-w-md text-sm text-sage-600">{t("result.moreExploration")}</p>
        <Link to="/app/passport" className="btn-primary shrink-0">
          {t("result.buildPassport")}
        </Link>
      </div>
    </div>
  );
}

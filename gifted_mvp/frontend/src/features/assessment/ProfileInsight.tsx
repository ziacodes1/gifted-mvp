import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { ProfileInsight } from "../../types/ai";
import type { SignalResult } from "../../types/assessment";
import { iconForSignal } from "../../utils/signalIcons";

const LOADING_STEPS = ["insight.loading.connecting", "insight.loading.patterns", "insight.loading.preparing"];

/** Lightweight generation state: rotating copy + skeleton, no fake percentages. */
export function InsightLoading() {
  const { t } = useTranslation();
  const [step, setStep] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setStep((s) => Math.min(s + 1, LOADING_STEPS.length - 1)), 2200);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="card mt-6" aria-busy="true" aria-live="polite">
      <div className="flex items-center gap-3">
        <span className="relative flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-gold-400 opacity-60" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-gold-500" />
        </span>
        <p key={step} className="animate-fade-in text-sm font-medium text-forest-700">
          {t(LOADING_STEPS[step])}
        </p>
      </div>
      <div className="mt-5 grid gap-6 md:grid-cols-[1.4fr_1fr]">
        <div className="space-y-3">
          <div className="h-5 w-3/4 animate-pulse rounded bg-cream-200" />
          <div className="h-3 w-full animate-pulse rounded bg-cream-100" />
          <div className="h-3 w-11/12 animate-pulse rounded bg-cream-100" />
          <div className="h-3 w-2/3 animate-pulse rounded bg-cream-100" />
        </div>
        <div className="space-y-3 md:border-l md:border-cream-200 md:pl-6">
          <div className="h-4 w-1/3 animate-pulse rounded bg-cream-200" />
          <div className="h-3 w-full animate-pulse rounded bg-cream-100" />
          <div className="h-9 w-2/3 animate-pulse rounded-xl bg-cream-100" />
        </div>
      </div>
    </div>
  );
}

function AiBadge({ source }: { source: ProfileInsight["source"] }) {
  const { t } = useTranslation();
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full border border-cream-200 bg-cream-50 px-2.5 py-0.5 text-[11px] font-medium text-sage-600"
      title={source === "AI" ? t("insight.badge.aiTitle") : t("insight.badge.signalTitle")}
    >
      <span aria-hidden>✦</span> {source === "AI" ? t("insight.badge.ai") : t("insight.badge.signal")}
    </span>
  );
}

/** Overall insight + Next step (reference layout: two-column hero card). */
export function InsightHero({ insight, signals }: { insight: ProfileInsight; signals: SignalResult[] }) {
  const { t } = useTranslation();
  const { profile, next_step } = insight;
  const labelFor = (key: string) => signals.find((s) => s.key === key)?.label ?? key;

  return (
    <div className="card mt-6 grid gap-6 md:grid-cols-[1.4fr_1fr]">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs font-medium uppercase tracking-widest text-sage-600">{t("insight.overall")}</p>
          <AiBadge source={insight.source} />
        </div>
        <h2 className="mt-2 text-xl leading-snug text-forest-800">{profile.headline}</h2>
        <p className="mt-2 leading-relaxed text-forest-700">{profile.summary}</p>
        {profile.uncertainty_notes.length > 0 && (
          <div className="mt-4 rounded-xl bg-forest-50 px-4 py-3 text-sm text-forest-700">
            {profile.uncertainty_notes.map((n) => (
              <p key={n} className="[&+&]:mt-1">
                {n}
              </p>
            ))}
          </div>
        )}
      </div>

      <div className="md:border-l md:border-cream-200 md:pl-6">
        <p className="text-xs font-medium uppercase tracking-widest text-gold-600">{t("dashboard.next.eyebrow")}</p>
        <h3 className="mt-2 text-lg leading-snug text-forest-800">{next_step.title}</h3>
        <span className="mt-1 inline-block rounded-full bg-gold-50 px-2 py-0.5 text-[11px] font-medium capitalize text-gold-600">
          {t(`activity.${next_step.activity_type}`, { defaultValue: next_step.activity_type })}
        </span>
        <p className="mt-3 text-sm leading-relaxed text-forest-700">{next_step.reason}</p>
        <dl className="mt-3 space-y-2 text-sm">
          <div>
            <dt className="text-xs font-medium text-sage-600">{t("insight.basedOn")}</dt>
            <dd className="mt-1 flex flex-wrap gap-1.5">
              {next_step.signals_used.map((k) => (
                <span key={k} className="rounded-full bg-forest-50 px-2 py-0.5 text-xs text-forest-700">
                  {iconForSignal(k)} {labelFor(k)}
                </span>
              ))}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-sage-600">{t("insight.helpsClarify")}</dt>
            <dd className="text-forest-700">{next_step.intended_validation}</dd>
          </div>
        </dl>
        <p className="mt-3 text-xs italic text-sage-600">{next_step.confidence_note}</p>
      </div>
    </div>
  );
}

/** Emerging strengths + areas needing more evidence. */
export function InsightDetails({ insight }: { insight: ProfileInsight }) {
  const { t } = useTranslation();
  const { profile } = insight;
  return (
    <div className="mt-8 grid gap-4 md:grid-cols-2">
      <div className="card">
        <h2 className="text-lg">{t("insight.strengths")}</h2>
        <ul className="mt-3 space-y-3">
          {profile.emerging_strengths.map((s) => (
            <li key={s.title}>
              <p className="font-medium text-forest-700">{s.title}</p>
              <p className="text-sm text-sage-600">{s.reason}</p>
            </li>
          ))}
        </ul>
      </div>
      <div className="card">
        <h2 className="text-lg">{t("insight.exploreFurther")}</h2>
        <p className="text-sm text-sage-600">{t("insight.exploreFurtherNote")}</p>
        {profile.exposure_gaps.length > 0 && (
          <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-forest-700">
            {profile.exposure_gaps.map((g) => (
              <li key={g}>{g}</li>
            ))}
          </ul>
        )}
        {profile.suggested_explorations.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {profile.suggested_explorations.map((e) => (
              <span key={e} className="rounded-full border border-cream-200 bg-cream-50 px-3 py-1 text-xs text-forest-700">
                {e}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

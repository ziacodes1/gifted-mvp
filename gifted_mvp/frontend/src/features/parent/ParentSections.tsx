import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import type { ParentInsight, ParentOverview } from "../../types/parent";
import { iconForSignal } from "../../utils/signalIcons";
import { ArrowIcon, ChartIcon, CheckIcon, CompassIcon, DocIcon, LeafIcon, QuoteIcon, SparkIcon } from "../passport/icons";
import { SignalStrength } from "../passport/PassportSections";

const STATUS_LABEL = { EMPTY: "passport.status.empty", EMERGING: "passport.status.emerging", GROWING: "passport.status.growing" } as const;

export function LearnerChips({ data }: { data: ParentOverview }) {
  const { t } = useTranslation();
  return (
    <div className="mt-5 flex flex-wrap items-center gap-2 text-xs">
      <span className="inline-flex items-center gap-1.5 rounded-full bg-forest-700 px-3 py-1 font-medium text-cream-50">
        <span className="h-1.5 w-1.5 rounded-full bg-gold-400" /> {t(STATUS_LABEL[data.status])}
      </span>
      {data.learner.journey_stage && (
        <span className="rounded-full border border-forest-700/15 bg-white/80 px-3 py-1 text-forest-700">
          {t("parent.chips.stage", { stage: data.learner.journey_stage })}
        </span>
      )}
      <span className="rounded-full border border-forest-700/15 bg-white/80 px-3 py-1 text-forest-700">
        {data.learner.passport_number}
      </span>
    </div>
  );
}

export function PrivacyNote({ text }: { text: string }) {
  return (
    <p className="flex items-center gap-2 text-xs text-sage-600">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className="h-3.5 w-3.5" aria-hidden>
        <rect x="5" y="10.5" width="14" height="9.5" rx="2" />
        <path d="M8.5 10.5V8a3.5 3.5 0 0 1 7 0v2.5" />
      </svg>
      {text}
    </p>
  );
}

export function CardTitle({ icon, title, aside }: { icon: ReactNode; title: string; aside?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center gap-2.5">
        <span className="grid h-9 w-9 place-items-center rounded-full bg-forest-50 text-forest-700">{icon}</span>
        <h2 className="text-lg">{title}</h2>
      </div>
      {aside}
    </div>
  );
}

export function InsightBadge({ source }: { source: ParentInsight["source"] }) {
  const { t } = useTranslation();
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-gold-400/40 bg-gold-50 px-2.5 py-0.5 text-[11px] font-medium text-gold-600">
      <SparkIcon className="h-3.5 w-3.5" /> {source === "AI" ? t("insight.badge.ai") : t("parent.signalGuidance")}
    </span>
  );
}

/** C. 2–3 strongest assessment signals, no labels or careers. */
export function CurrentPicture({ data, limit = 3 }: { data: ParentOverview; limit?: number }) {
  const { t } = useTranslation();
  const signals = (data.current_signals ?? []).slice(0, limit);
  const answered = data.evidence?.assessment ?? 0;
  return (
    <div className="card">
      <CardTitle
        icon={<ChartIcon className="h-4 w-4" />}
        title={t("parent.picture.title")}
        aside={<span className="text-[11px] uppercase tracking-wider text-sage-600">{t("passport.tags.calculated")}</span>}
      />
      <ul className="mt-5 space-y-4">
        {signals.map((s) => (
          <li key={s.key}>
            <div className="flex items-baseline justify-between gap-3">
              <span className="flex items-center gap-2 font-medium text-forest-700">
                <span aria-hidden>{iconForSignal(s.key)}</span> {s.label}
              </span>
              <span className="font-serif text-lg text-forest-700">{s.score}%</span>
            </div>
            <div className="mt-2">
              <SignalStrength score={s.score} confidence={s.confidence} />
            </div>
            <p className="mt-1.5 text-xs text-sage-600">
              {t(`passport.signalLevel.${s.confidence}`)} ·{" "}
              {t("parent.picture.picked", { picked: s.evidence_count, total: s.opportunity_count || answered })}
            </p>
          </li>
        ))}
      </ul>
      <p className="mt-4 text-xs text-sage-600">{t("parent.picture.note")}</p>
    </div>
  );
}

/** D. Real evidence counts. */
export function EvidenceCounts({ evidence }: { evidence: NonNullable<ParentOverview["evidence"]> }) {
  const { t } = useTranslation();
  const rows = [
    { label: t("passport.evidence.assessment"), value: evidence.assessment },
    { label: t("passport.evidence.missions"), value: evidence.missions },
    { label: t("parent.evidence.realWorld"), value: evidence.experiences + evidence.opportunities },
  ];
  return (
    <div className="card">
      <CardTitle icon={<DocIcon className="h-4 w-4" />} title={t("passport.evidence.title")} />
      <ul className="mt-4 divide-y divide-cream-200">
        {rows.map((r) => (
          <li key={r.label} className="flex items-center justify-between py-2.5 text-sm">
            <span className={r.value ? "text-forest-700" : "text-sage-600"}>{r.label}</span>
            <span className={`font-serif text-lg ${r.value ? "text-forest-700" : "text-sage-400"}`}>{r.value}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-sage-600">
        {evidence.missions > 0 ? t("parent.evidence.varied") : t("parent.evidence.oneAssessment")}
      </p>
    </div>
  );
}

export function InsightLoadingCard() {
  const { t } = useTranslation();
  return (
    <div className="card" aria-busy="true">
      <div className="flex items-center gap-3">
        <span className="relative flex h-2.5 w-2.5">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-gold-400 opacity-60" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-gold-500" />
        </span>
        <p className="text-sm font-medium text-forest-700">{t("parent.preparing")}</p>
      </div>
      <div className="mt-4 space-y-2.5">
        <div className="h-3 w-full animate-pulse rounded bg-cream-100" />
        <div className="h-3 w-11/12 animate-pulse rounded bg-cream-100" />
        <div className="h-3 w-2/3 animate-pulse rounded bg-cream-100" />
      </div>
    </div>
  );
}

/** E. Parent insight summary (dashboard). */
export function ParentInsightSummary({ insight }: { insight: ParentInsight }) {
  const { t } = useTranslation();
  const c = insight.content;
  return (
    <div className="card flex flex-col bg-gradient-to-br from-white to-forest-50/60">
      <CardTitle icon={<LeafIcon className="h-4 w-4" />} title={t("parent.learning")} aside={<InsightBadge source={insight.source} />} />
      <p className="mt-4 font-serif text-xl leading-snug text-forest-700">{c.summary}</p>
      <ul className="mt-4 space-y-2">
        {c.what_we_are_seeing.slice(0, 2).map((s) => (
          <li key={s.title} className="flex gap-2 text-sm text-forest-700">
            <CheckIcon className="mt-0.5 h-4 w-4 shrink-0 text-forest-600" />
            <span>
              <span className="font-medium">{s.title}.</span> <span className="text-sage-600">{s.explanation}</span>
            </span>
          </li>
        ))}
      </ul>
      <Link to="/parent/insights" className="mt-auto inline-flex items-center gap-1.5 pt-5 text-sm font-medium text-forest-700 hover:underline">
        {t("parent.readFull")} <ArrowIcon />
      </Link>
    </div>
  );
}

/** F. Evidence limits — framed as open questions. */
export function StillUnclear({ items }: { items: string[] }) {
  const { t } = useTranslation();
  return (
    <div className="card">
      <CardTitle icon={<CompassIcon className="h-4 w-4" />} title={t("parent.unclear")} />
      <ul className="mt-4 space-y-2.5">
        {items.map((item) => (
          <li key={item} className="rounded-xl bg-cream-50 px-4 py-3 text-sm leading-relaxed text-forest-700">
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

/** G. Practical support — nothing to buy. */
export function SupportAtHome({ items }: { items: ParentInsight["content"]["support_at_home"] }) {
  const { t } = useTranslation();
  return (
    <div className="card">
      <CardTitle
        icon={
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className="h-4 w-4" aria-hidden>
            <path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10Z" />
          </svg>
        }
        title={t("parent.support")}
      />
      <ul className="mt-4 space-y-3">
        {items.map((s, i) => (
          <li key={s.title} className="flex gap-3">
            <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-gold-50 text-xs font-semibold text-gold-600">
              {i + 1}
            </span>
            <div>
              <p className="font-medium text-forest-700">{s.title}</p>
              <p className="text-sm leading-relaxed text-sage-600">{s.action}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

/** H. The child's current next exploration. */
export function NextExploration({ data }: { data: ParentOverview }) {
  const { t } = useTranslation();
  const m = data.next_mission;
  const step = data.next_step;
  const done = m?.status === "COMPLETED";
  return (
    <div className="rounded-3xl bg-forest-700 p-6 text-cream-50 shadow-card sm:p-8">
      <div className="grid gap-6 md:grid-cols-[1.2fr_1fr] md:items-center">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-gold-400">{t("parent.next.eyebrow")}</p>
          {step && <h2 className="mt-3 text-2xl leading-snug text-cream-50 md:text-3xl">{step.title}</h2>}
          {step && step.signals.length > 0 && (
            <p className="mt-2 text-sm text-cream-50/75">{t("parent.next.connected", { signals: step.signals.join(", ") })}</p>
          )}
          <p className="mt-4 max-w-lg text-sm leading-relaxed text-cream-50/70">{t("parent.next.note")}</p>
        </div>
        {m && (
          <div className="rounded-2xl bg-cream-50/[0.07] p-5 ring-1 ring-cream-50/10">
            <p className="text-xs font-medium uppercase tracking-wider text-gold-400">
              {done ? t("parent.next.completed") : m.status === "IN_PROGRESS" ? t("parent.next.inProgress") : t("parent.next.available")}
            </p>
            <p className="mt-2 font-serif text-xl text-cream-50">{m.title}</p>
            <p className="mt-1 text-sm leading-relaxed text-cream-50/75">{m.short_description}</p>
            <p className="mt-3 text-xs text-cream-50/60">
              {m.time_label} · {t("parent.next.explores", { areas: m.focus_areas.slice(0, 3).join(", ").toLowerCase() })}
            </p>
            {done && (
              <p className="mt-3 inline-flex items-center gap-2 text-sm text-cream-50">
                <CheckIcon /> {t("parent.next.added")}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export function ConversationStarter({ text, caution }: { text: string; caution: string }) {
  const { t } = useTranslation();
  return (
    <div className="rounded-3xl border border-cream-200 bg-cream-50 px-6 py-6 md:px-8">
      <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-600">{t("parent.starter")}</p>
      <div className="mt-3 flex gap-3">
        <QuoteIcon className="h-6 w-6 shrink-0 text-gold-400" />
        <p className="font-serif text-2xl italic leading-snug text-forest-700">{text}</p>
      </div>
      <div className="mt-4 h-0.5 w-10 rounded-full bg-gold-500" />
      <p className="mt-4 text-sm text-sage-600">{caution}</p>
    </div>
  );
}

/** No-evidence state: no charts, no zeroes. */
export function DiscoveryNotStarted({ name, privacy }: { name: string; privacy: string }) {
  const { t } = useTranslation();
  const later = [t("parent.notStarted.later.signals"), t("parent.notStarted.later.explored"), t("parent.notStarted.later.ideas")];
  return (
    <div className="card mt-6 md:p-10">
      <span className="inline-flex items-center gap-1.5 rounded-full border border-forest-700/15 bg-cream-50 px-3 py-1 text-xs font-medium text-forest-700">
        <span className="h-1.5 w-1.5 rounded-full bg-sage-400" /> {t("passport.empty.badge")}
      </span>
      <h2 className="mt-4 text-3xl leading-tight">{t("parent.notStarted.title")}</h2>
      <p className="mt-3 max-w-2xl leading-relaxed text-sage-600">{t("parent.notStarted.text", { name })}</p>
      <ul className="mt-5 space-y-2.5">
        {later.map((item) => (
          <li key={item} className="flex gap-3 text-forest-700">
            <LeafIcon className="mt-0.5 h-4 w-4 shrink-0" /> {item}
          </li>
        ))}
      </ul>
      <div className="mt-6">
        <PrivacyNote text={privacy} />
      </div>
    </div>
  );
}

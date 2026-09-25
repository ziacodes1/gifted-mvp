import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import type { MissionSummary } from "../../types/mission";
import type { EmergingStrength } from "../../types/ai";
import type {
  EvidenceItem,
  EvidenceSummary as Evidence,
  ExploredDimension,
  JourneyStage,
  PassportNextStep,
  PassportSignal,
} from "../../types/passport";
import { iconForSignal } from "../../utils/signalIcons";
import { ArrowIcon, ChartIcon, CheckIcon, CompassIcon, DocIcon, LeafIcon, SparkIcon } from "./icons";

/** Section header with an icon tile and an optional provenance tag on the right. */
export function SectionHeader({
  icon,
  title,
  subtitle,
  tag,
}: {
  icon: ReactNode;
  title: string;
  subtitle?: string;
  tag?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-forest-50 text-forest-700">
          {icon}
        </span>
        <div>
          <h2 className="text-xl">{title}</h2>
          {subtitle && <p className="mt-0.5 text-sm text-sage-600">{subtitle}</p>}
        </div>
      </div>
      {tag}
    </div>
  );
}

/** Provenance tag: keeps calculated values visually distinct from AI interpretation. */
export function SourceTag({ kind }: { kind: "calculated" | "recorded" | "AI" | "FALLBACK" }) {
  if (kind === "recorded") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-forest-700/15 bg-white/70 px-3 py-1 text-[11px] font-medium uppercase tracking-wider text-forest-700">
        <DocIcon className="h-3.5 w-3.5" /> Recorded evidence
      </span>
    );
  }
  if (kind === "calculated") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-forest-700/15 bg-white/70 px-3 py-1 text-[11px] font-medium uppercase tracking-wider text-forest-700">
        <ChartIcon className="h-3.5 w-3.5" /> Assessment signals
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-gold-400/40 bg-gold-50 px-3 py-1 text-[11px] font-medium uppercase tracking-wider text-gold-600">
      <SparkIcon className="h-3.5 w-3.5" /> {kind === "AI" ? "AI-assisted insight" : "Signal-based insight"}
    </span>
  );
}

const CONFIDENCE: Record<PassportSignal["confidence"], { label: string; bar: string; chip: string }> = {
  HIGH: { label: "Consistent", bar: "bg-forest-700", chip: "bg-forest-50 text-forest-700" },
  MEDIUM: { label: "Developing", bar: "bg-forest-600/70", chip: "bg-forest-50 text-forest-600" },
  LOW: { label: "Early", bar: "bg-gold-400", chip: "bg-gold-50 text-gold-600" },
};

/** Strength bar for one assessment signal score. */
export function SignalStrength({ score, confidence }: { score: number; confidence: PassportSignal["confidence"] }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-cream-200" role="presentation">
      <div className={`h-full rounded-full ${CONFIDENCE[confidence].bar}`} style={{ width: `${score}%` }} />
    </div>
  );
}

/** B. One calculated signal. */
export function SignalCard({ signal, answered }: { signal: PassportSignal; answered: number }) {
  const c = CONFIDENCE[signal.confidence];
  return (
    <div className="rounded-2xl border border-cream-200/80 bg-white p-5 shadow-soft">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-full bg-cream-100 text-lg">
            {iconForSignal(signal.key)}
          </span>
          <p className="font-medium leading-tight text-forest-700">{signal.label}</p>
        </div>
        <p className="font-serif text-2xl text-forest-700">
          {signal.score}
          <span className="text-sm text-sage-600">%</span>
        </p>
      </div>
      <div className="mt-4">
        <SignalStrength score={signal.score} confidence={signal.confidence} />
      </div>
      <div className="mt-3 flex items-center justify-between text-xs">
        <span className={`rounded-full px-2 py-0.5 font-medium ${c.chip}`}>{c.label} signal</span>
        <span className="text-sage-600">
          Picked {signal.evidence_count} of {signal.opportunity_count || answered} times
        </span>
      </div>
    </div>
  );
}

/** Journey progress strip (reference: "Your Journey Progress"). Only earned stages are checked. */
export function JourneyProgress({
  stages,
  note,
  title = "Your journey",
}: {
  stages: JourneyStage[];
  note?: ReactNode;
  title?: string;
}) {
  const done = stages.filter((s) => s.done).length;
  return (
    <div className="card flex flex-col">
      <div className="flex items-baseline justify-between">
        <h3 className="text-lg">{title}</h3>
        <span className="text-sm text-sage-600">
          {done} of {stages.length}
        </span>
      </div>
      <ol className="my-6 flex items-start">
        {stages.map((s, i) => {
          const current = !s.done && (i === 0 || stages[i - 1].done);
          return (
            <li key={s.key} className="flex flex-1 flex-col items-center">
              <div className="flex w-full items-center">
                <div className={`h-px flex-1 ${i === 0 ? "opacity-0" : s.done || current ? "bg-forest-700" : "bg-sage-200"}`} />
                <span
                  className={`grid h-8 w-8 shrink-0 place-items-center rounded-full text-xs font-semibold ${
                    s.done
                      ? "bg-forest-700 text-cream-50"
                      : current
                        ? "border-2 border-forest-700 bg-white text-forest-700"
                        : "border border-sage-200 bg-white text-sage-600"
                  }`}
                >
                  {s.done ? <CheckIcon /> : i + 1}
                </span>
                <div className={`h-px flex-1 ${i === stages.length - 1 ? "opacity-0" : s.done ? "bg-forest-700" : "bg-sage-200"}`} />
              </div>
              <span className={`mt-2 text-xs ${s.done || current ? "font-medium text-forest-700" : "text-sage-600"}`}>
                {s.label}
              </span>
            </li>
          );
        })}
      </ol>
      <div className="mt-auto flex items-start gap-3 rounded-2xl bg-forest-50 px-4 py-3 pt-3">
        <LeafIcon className="mt-0.5 h-5 w-5 shrink-0 text-forest-700" />
        <p className="text-sm leading-relaxed text-forest-700">
          {note ?? (done >= 2 ? (
            <>
              <span className="font-medium">Discover and Explore are under way.</span> Validate opens as more varied
              evidence — more missions and real experiences — builds up.
            </>
          ) : done === 1 ? (
            <>
              <span className="font-medium">Discover is complete.</span> Explore opens with your first mission — see
              your next exploration below.
            </>
          ) : (
            "Your journey begins with the Discovery assessment."
          ))}
        </p>
      </div>
    </div>
  );
}

/** D. What the Passport is based on — real counts only. */
export function EvidenceSummary({
  evidence,
  sources,
}: {
  evidence: Evidence;
  sources: { assessments: number; missions: number };
}) {
  const rows = [
    { label: "Assessment responses", value: evidence.assessment },
    { label: "Exploration missions", value: evidence.missions },
    { label: "Real-world experiences", value: evidence.experiences },
  ];
  return (
    <div className="card">
      <div className="flex items-center gap-2">
        <DocIcon className="h-5 w-5 text-gold-500" />
        <h3 className="text-lg">Evidence so far</h3>
      </div>
      <ul className="mt-4 divide-y divide-cream-200">
        {rows.map((r) => (
          <li key={r.label} className="flex items-center justify-between py-2.5 text-sm">
            <span className={r.value ? "text-forest-700" : "text-sage-600"}>{r.label}</span>
            <span className={`font-serif text-lg ${r.value ? "text-forest-700" : "text-sage-400"}`}>{r.value}</span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-sage-600">
        {sources.missions > 0
          ? `Your profile now includes evidence from ${plural(sources.assessments, "assessment")} and ${plural(sources.missions, "exploration mission")}.`
          : "Your Passport is still early — every new activity adds evidence."}
      </p>
    </div>
  );
}

function plural(n: number, word: string) {
  return `${n} ${word}${n === 1 ? "" : "s"}`;
}

/** Non-assessment evidence: what was recorded, and which dimensions it touched. Not scores. */
export function ExplorationEvidence({ items, dimensions }: { items: EvidenceItem[]; dimensions: ExploredDimension[] }) {
  return (
    <div className="grid gap-5 md:grid-cols-[1.3fr_1fr] md:items-start">
      <div className="card">
        <h3 className="text-lg">Evidence log</h3>
        <ul className="mt-4 space-y-4">
          {items.map((e) => (
            <li key={e.id} className="flex gap-4">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gold-50 text-gold-600">
                <CompassIcon className="h-5 w-5" />
              </span>
              <div className="min-w-0">
                <p className="font-medium text-forest-700">{e.title}</p>
                <p className="text-xs text-sage-600">
                  {e.source_label} ·{" "}
                  {new Date(e.created_at).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" })}
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {e.dimensions.map((d) => (
                    <span key={d.key} className="rounded-full bg-cream-100 px-2.5 py-0.5 text-xs text-forest-700">
                      {d.label}
                    </span>
                  ))}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
      <div className="card">
        <h3 className="text-lg">Explored so far</h3>
        <p className="mt-0.5 text-sm text-sage-600">What your activities gave evidence of.</p>
        <ul className="mt-4 divide-y divide-cream-200">
          {dimensions.map((d) => (
            <li key={d.key} className="flex items-center justify-between gap-3 py-2.5">
              <span className="text-sm text-forest-700">{d.label}</span>
              <span className="shrink-0 text-right text-xs text-sage-600">{d.kinds.join(" · ")}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-xs text-sage-600">One activity is a single data point — it adds context, not a verdict.</p>
      </div>
    </div>
  );
}

/** C. One emerging strength from the saved interpretation. */
export function EmergingStrengthCard({ strength }: { strength: EmergingStrength }) {
  return (
    <li className="flex gap-3">
      <span className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full bg-forest-50 text-forest-700">
        <LeafIcon className="h-4 w-4" />
      </span>
      <div>
        <p className="font-medium text-forest-700">{strength.title}</p>
        <p className="mt-0.5 text-sm leading-relaxed text-sage-600">{strength.reason}</p>
      </div>
    </li>
  );
}

/** E. One area worth exploring — phrased as an open question, never a deficit. */
export function ExplorationGapCard({ text }: { text: string }) {
  return (
    <li className="flex gap-3 rounded-xl bg-cream-50 px-4 py-3 text-sm leading-relaxed text-forest-700">
      <CompassIcon className="mt-0.5 h-4 w-4 shrink-0 text-gold-500" />
      <span>{text}</span>
    </li>
  );
}

/** F. The persisted next-step recommendation, connected to the mission it (honestly) maps to. */
export function NextStepCard({
  step,
  source,
  mission,
}: {
  step: PassportNextStep;
  source: "AI" | "FALLBACK" | null;
  mission: MissionSummary | null;
}) {
  const done = mission?.my_attempt?.status === "COMPLETED";
  const inProgress = mission?.my_attempt?.status === "IN_PROGRESS";
  const recommended = mission?.match === "RECOMMENDED";

  return (
    <div className="rounded-3xl bg-forest-700 p-6 text-cream-50 shadow-card sm:p-8">
      <div className="grid gap-8 lg:grid-cols-[1.3fr_1fr]">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-gold-400">Your next exploration</p>
          <h2 className="mt-3 text-2xl leading-snug text-cream-50 md:text-3xl">{step.title}</h2>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-full bg-gold-500/90 px-2.5 py-0.5 font-medium capitalize text-forest-900">
              {step.activity_type}
            </span>
            {step.signals_used.map((s) => (
              <span key={s.key} className="rounded-full bg-cream-50/10 px-2.5 py-0.5 text-cream-50/90">
                {iconForSignal(s.key)} {s.label}
              </span>
            ))}
          </div>
          <p className="mt-4 max-w-xl leading-relaxed text-cream-50/85">{step.reason}</p>
          <p className="mt-4 text-xs text-cream-50/60">
            <span className="text-gold-400">What this helps clarify:</span> {step.intended_validation}
          </p>
          {source === "AI" && <p className="mt-2 text-xs italic text-cream-50/50">Suggested with AI from your current signals.</p>}
        </div>

        {mission && (
          <div className="flex flex-col rounded-2xl bg-cream-50/[0.07] p-5 ring-1 ring-cream-50/10">
            <p className="text-xs font-medium uppercase tracking-wider text-gold-400">
              {done ? "Exploration completed" : recommended ? "Start with this mission" : "A useful next exploration"}
            </p>
            <p className="mt-2 font-serif text-xl text-cream-50">{mission.title}</p>
            <p className="mt-1 text-sm leading-relaxed text-cream-50/75">{mission.short_description}</p>
            <p className="mt-3 text-xs text-cream-50/60">
              {mission.time_label} · {mission.activity_label}
            </p>
            <div className="mt-auto pt-5">
              {done ? (
                <>
                  <p className="inline-flex items-center gap-2 text-sm font-medium text-cream-50">
                    <CheckIcon /> Added to your Passport evidence
                  </p>
                  <Link
                    to={`/app/missions/${mission.slug}`}
                    className="mt-3 block text-sm text-gold-400 underline-offset-2 hover:underline"
                  >
                    View what you added →
                  </Link>
                </>
              ) : (
                <>
                  <Link
                    to={`/app/missions/${mission.slug}`}
                    className="inline-flex items-center gap-2 rounded-full bg-gold-500 px-5 py-2.5 text-sm font-medium text-forest-900 transition hover:bg-gold-400"
                  >
                    {inProgress ? "Continue mission" : recommended ? "Explore this next" : "Try this mission"} <ArrowIcon />
                  </Link>
                  {!recommended && (
                    <p className="mt-2 text-xs text-cream-50/60">
                      A general exploration that adds a different kind of evidence — not tailored to the suggestion on the
                      left.
                    </p>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/** G. Evolving-profile principle. */
export function EvolvingMessage({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-4 rounded-3xl border border-cream-200 bg-cream-50 px-6 py-5">
      <LeafIcon className="mt-1 h-6 w-6 shrink-0 text-forest-700" />
      <div>
        <p className="font-serif text-lg italic leading-snug text-forest-700">{message}</p>
        <div className="mt-3 h-0.5 w-10 rounded-full bg-gold-500" />
      </div>
    </div>
  );
}

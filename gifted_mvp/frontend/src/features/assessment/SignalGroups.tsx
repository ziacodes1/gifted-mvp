import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { PassportSignal } from "../../types/passport";
import { CheckIcon, CompassIcon, LeafIcon, SparkIcon } from "../passport/icons";

type Signal = Pick<PassportSignal, "key" | "label" | "category" | "confidence" | "evidence_count" | "opportunity_count">;

function Group({ icon, title, note, children }: { icon: ReactNode; title: string; note: string; children: ReactNode }) {
  return (
    <div className="rounded-2xl border border-cream-200/80 bg-white p-5 shadow-soft">
      <div className="flex items-center gap-2.5">
        <span className="grid h-8 w-8 place-items-center rounded-full bg-forest-50 text-forest-700">{icon}</span>
        <p className="font-serif text-lg text-forest-700">{title}</p>
      </div>
      <div className="mt-3">{children}</div>
      <p className="mt-3 text-xs leading-relaxed text-sage-600">{note}</p>
    </div>
  );
}

function Chip({ children, muted = false }: { children: ReactNode; muted?: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm ${
        muted ? "border border-dashed border-sage-200 text-sage-600" : "bg-forest-50 text-forest-700"
      }`}
    >
      {children}
    </span>
  );
}

/** Non-interest signals, grouped by type. Only groups with real evidence render;
 * exposure also lists what hasn't been tried yet (an open door, not a gap in ability). */
export function SignalGroups({ signals, voice = "you" }: { signals: Signal[]; voice?: "you" | "they" }) {
  const { t } = useTranslation();
  const by = (cat: string, withEvidence = true) =>
    signals.filter((s) => s.category === cat && (withEvidence ? s.evidence_count > 0 : s.evidence_count === 0));
  const reasoning = by("APTITUDE");
  const style = by("WORK_STYLE");
  const values = by("VALUE");
  const tried = by("EXPOSURE");
  const notTried = by("EXPOSURE", false);
  const hasExposureQuestion = tried.length + notTried.length > 0;

  if (!reasoning.length && !style.length && !values.length && !hasExposureQuestion) return null;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {reasoning.length > 0 && (
        <Group
          icon={<SparkIcon className="h-4 w-4" />}
          title={t("signals.groups.reasoning.title")}
          note={t("signals.groups.reasoning.note")}
        >
          <div className="flex flex-wrap gap-2">
            {reasoning.map((s) => (
              <Chip key={s.key}>
                <CheckIcon className="h-3.5 w-3.5" /> {t("signals.groups.reasoning.chip", { label: s.label })}
              </Chip>
            ))}
          </div>
        </Group>
      )}
      {style.length > 0 && (
        <Group icon={<CompassIcon className="h-4 w-4" />} title={t("signals.groups.style.title")} note={t(`signals.groups.style.note_${voice}`)}>
          <ul className="space-y-1.5">
            {style.map((s) => (
              <li key={s.key} className="flex items-center justify-between gap-3 text-sm text-forest-700">
                {s.label}
                <span className="text-xs text-sage-600">{s.confidence === "MEDIUM" ? t("signals.groups.style.clear") : t("signals.groups.style.hint")}</span>
              </li>
            ))}
          </ul>
        </Group>
      )}
      {values.length > 0 && (
        <Group icon={<LeafIcon className="h-4 w-4" />} title={t("signals.groups.values.title")} note={t("signals.groups.values.note")}>
          <div className="flex flex-wrap gap-2">
            {values.map((s) => (
              <Chip key={s.key}>{s.label}</Chip>
            ))}
          </div>
        </Group>
      )}
      {hasExposureQuestion && (
        <Group
          icon={
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} className="h-4 w-4" aria-hidden>
              <path d="M4 19h16M6 15l4-4 3 3 5-6" />
            </svg>
          }
          title={t("signals.groups.exposure.title")}
          note={t("signals.groups.exposure.note")}
        >
          {tried.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {tried.map((s) => (
                <Chip key={s.key}>
                  <CheckIcon className="h-3.5 w-3.5" /> {s.label}
                </Chip>
              ))}
            </div>
          )}
          {notTried.length > 0 && (
            <div className={`flex flex-wrap gap-2 ${tried.length ? "mt-2" : ""}`}>
              {notTried.map((s) => (
                <Chip key={s.key} muted>
                  {t("signals.groups.exposure.notTried", { label: s.label })}
                </Chip>
              ))}
            </div>
          )}
        </Group>
      )}
    </div>
  );
}

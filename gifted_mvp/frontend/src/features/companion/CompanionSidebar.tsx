import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { BulbIcon, ChevronIcon, CompassIcon, LeafIcon, LockIcon, UserIcon } from "../passport/icons";
import type { CompanionAbout, SuggestedPrompt } from "../../types/companion";

function SideCard({ icon, title, subtitle, tag, children }: { icon: ReactNode; title: string; subtitle?: string; tag?: ReactNode; children?: ReactNode }) {
  return (
    <section className="rounded-3xl border border-cream-200/60 bg-white p-5 shadow-card">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-forest-50 text-forest-700">{icon}</span>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h2 className="text-xl leading-tight">{title}</h2>
            {tag}
          </div>
          {subtitle && <p className="mt-0.5 text-sm leading-snug text-sage-600">{subtitle}</p>}
        </div>
      </div>
      {children && <div className="mt-4">{children}</div>}
    </section>
  );
}

function Chip({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-cream-200 bg-cream-50 px-3 py-1.5 text-xs text-forest-700">
      {children}
    </span>
  );
}

/** What the Companion knows — shown so nothing about personalization is hidden. */
export function AboutYouCard({ about, loading }: { about?: CompanionAbout; loading: boolean }) {
  const { t } = useTranslation();
  const join = (items: string[]) => items.join(", ");
  return (
    <SideCard icon={<UserIcon />} title={t("companion.about.title")} subtitle={t("companion.about.subtitle")}>
      {loading ? (
        <div className="h-16 animate-pulse rounded-2xl bg-cream-100" />
      ) : !about ? null : about.passport_status === "EMPTY" ? (
        <div className="rounded-2xl bg-cream-50 p-4">
          <p className="text-sm leading-relaxed text-forest-700">{t("companion.about.empty")}</p>
          <Link to="/app/assessment" className="btn-primary mt-3 px-4 py-2 text-xs">
            {t("companion.about.startAssessment")}
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {about.journey_stage && (
              <Chip>
                <CompassIcon className="h-3.5 w-3.5 text-gold-500" /> {t("companion.about.stage", { stage: about.journey_stage })}
              </Chip>
            )}
            {about.interests.length > 0 && (
              <Chip>
                <BulbIcon className="h-3.5 w-3.5 text-gold-500" /> {t("companion.about.interests", { list: join(about.interests) })}
              </Chip>
            )}
            {about.values.length > 0 && (
              <Chip>
                <LeafIcon className="h-3.5 w-3.5 text-gold-500" /> {t("companion.about.values", { list: join(about.values) })}
              </Chip>
            )}
            {about.missions_completed > 0 && <Chip>{t("companion.about.missions", { count: about.missions_completed })}</Chip>}
          </div>
          {about.next_exploration && (
            <p className="text-sm text-forest-700">
              <span className="text-sage-600">{t("companion.about.next")}: </span>
              {about.next_exploration}
            </p>
          )}
        </div>
      )}
      <p className="mt-3 text-xs leading-relaxed text-sage-600">{t("companion.about.unknown")}</p>
    </SideCard>
  );
}

export function SuggestedPrompts({
  prompts,
  loading,
  disabled,
  onPick,
}: {
  prompts: SuggestedPrompt[];
  loading: boolean;
  disabled: boolean;
  onPick: (text: string) => void;
}) {
  const { t } = useTranslation();
  return (
    <SideCard
      icon={<BulbIcon className="h-5 w-5 text-gold-600" />}
      title={t("companion.prompts.title")}
      subtitle={t("companion.prompts.subtitle")}
    >
      {loading ? (
        <div className="space-y-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="h-11 animate-pulse rounded-xl bg-cream-100" />
          ))}
        </div>
      ) : (
        <ul className="space-y-2">
          {prompts.map((p) => {
            const text = t(`companion.prompts.${p.key}`, p.params);
            return (
              <li key={p.key}>
                <button
                  onClick={() => onPick(text)}
                  disabled={disabled}
                  className="flex w-full items-center justify-between gap-3 rounded-xl border border-cream-200 px-3.5 py-2.5 text-left text-sm text-forest-700 transition hover:border-forest-700/20 hover:bg-forest-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <span className="flex items-center gap-2.5">
                    <LeafIcon className="h-4 w-4 shrink-0 text-gold-500" />
                    {text}
                  </span>
                  <ChevronIcon className="h-4 w-4 shrink-0 text-sage-600" />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </SideCard>
  );
}

export function PrivacyNotice() {
  const { t } = useTranslation();
  return (
    <div className="flex items-start gap-3 rounded-3xl border border-forest-700/10 bg-forest-50/70 px-5 py-4">
      <LockIcon className="mt-0.5 h-5 w-5 shrink-0 text-forest-700" />
      <div>
        <p className="text-sm font-medium text-forest-700">{t("companion.privacy.title")}</p>
        <p className="mt-0.5 text-xs leading-relaxed text-forest-700/80">{t("companion.privacy.text")}</p>
      </div>
    </div>
  );
}

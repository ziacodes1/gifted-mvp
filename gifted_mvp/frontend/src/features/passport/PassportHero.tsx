import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import passportBook from "../../assets/passport/gifted_passport_book.webp";
import waveBanner from "../../assets/passport/passport_wave_banner.webp";
import type { Passport } from "../../types/passport";
import { formatDate } from "../../utils/date";
import { SparkIcon } from "./icons";

/** Cream wave surface shared by the hero and the empty state. */
export function WaveSurface({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`relative overflow-hidden rounded-3xl border border-cream-200/80 bg-cream-50 bg-[length:100%_100%] bg-no-repeat shadow-card ${className}`}
      style={{ backgroundImage: `url(${waveBanner})` }}
    >
      {children}
    </div>
  );
}

export function PassportBook({ className = "" }: { className?: string }) {
  const { t } = useTranslation();
  return (
    <img
      src={passportBook}
      alt={t("landing.passport.title")}
      className={`select-none drop-shadow-[0_18px_24px_rgba(22,51,38,0.25)] ${className}`}
      draggable={false}
    />
  );
}

const STATUS_LABEL: Record<Passport["status"], string> = {
  EMPTY: "passport.status.empty",
  EMERGING: "passport.status.emerging",
  GROWING: "passport.status.growing",
};

/** A. Passport identity: book object, learner, status, saved headline, passport facts. */
export function PassportHero({ passport }: { passport: Passport }) {
  const { t, i18n } = useTranslation();
  const lang = i18n.resolvedLanguage;
  const currentStage = [...passport.journey].reverse().find((s) => s.done)?.label ?? t("passport.status.empty");

  return (
    <WaveSurface>
      <div className="grid items-center gap-6 p-6 sm:p-8 md:grid-cols-[auto_1fr] lg:grid-cols-[auto_1fr_auto] lg:gap-10">
        <PassportBook className="mx-auto w-36 -rotate-2 md:w-44" />

        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-gold-600">
            {t("passport.hero.discover")} <span className="mx-1.5 text-gold-400">•</span> {t("passport.hero.explore")}{" "}
            <span className="mx-1.5 text-gold-400">•</span> {t("passport.hero.become")}
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h2 className="text-2xl md:text-3xl">{passport.learner.display_name}</h2>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-forest-700 px-3 py-1 text-xs font-medium text-cream-50">
              <span className="h-1.5 w-1.5 rounded-full bg-gold-400" />
              {t(STATUS_LABEL[passport.status])}
            </span>
          </div>
          {passport.headline && (
            <>
              <p className="mt-4 max-w-xl font-serif text-xl italic leading-snug text-forest-700 md:text-[1.4rem]">
                {passport.headline}
              </p>
              <div className="mt-3 h-0.5 w-12 rounded-full bg-gold-500" />
              <p className="mt-3 inline-flex items-center gap-1.5 text-xs text-sage-600">
                <SparkIcon className="h-3.5 w-3.5 text-gold-500" />
                {passport.insight_source === "AI" ? t("passport.hero.aiHeadline") : t("passport.hero.signalHeadline")} ·{" "}
                {t("passport.hero.evolves")}
              </p>
            </>
          )}
        </div>

        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 border-cream-200 text-sm md:col-span-2 lg:col-span-1 lg:grid-cols-1 lg:border-l lg:pl-8">
          <Fact label={t("passport.hero.number")} value={passport.passport_number} />
          <Fact label={t("passport.hero.memberSince")} value={formatDate(passport.learner.member_since, lang)} />
          <Fact label={t("passport.hero.lastUpdated")} value={formatDate(passport.updated_at, lang)} />
          <Fact label={t("passport.hero.stage")} value={currentStage} />
        </dl>
      </div>
    </WaveSurface>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col lg:min-w-[11rem] lg:flex-row lg:items-baseline lg:justify-between lg:gap-4">
      <dt className="text-xs text-sage-600">{label}</dt>
      <dd className="font-medium text-forest-700">{value}</dd>
    </div>
  );
}

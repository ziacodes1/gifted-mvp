import type { ReactNode } from "react";
import passportBook from "../../assets/passport/gifted_passport_book.webp";
import waveBanner from "../../assets/passport/passport_wave_banner.webp";
import type { Passport } from "../../types/passport";
import { SparkIcon } from "./icons";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
}

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
  return (
    <img
      src={passportBook}
      alt="Gifted Passport"
      className={`select-none drop-shadow-[0_18px_24px_rgba(22,51,38,0.25)] ${className}`}
      draggable={false}
    />
  );
}

const STATUS_LABEL: Record<Passport["status"], string> = {
  EMPTY: "Not started",
  EMERGING: "Emerging Passport",
  GROWING: "Growing Passport",
};

/** A. Passport identity: book object, learner, status, saved headline, passport facts. */
export function PassportHero({ passport }: { passport: Passport }) {
  const currentStage = [...passport.journey].reverse().find((s) => s.done)?.label ?? "Not started";

  return (
    <WaveSurface>
      <div className="grid items-center gap-6 p-6 sm:p-8 md:grid-cols-[auto_1fr] lg:grid-cols-[auto_1fr_auto] lg:gap-10">
        <PassportBook className="mx-auto w-36 -rotate-2 md:w-44" />

        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-gold-600">
            Discover <span className="mx-1.5 text-gold-400">•</span> Explore{" "}
            <span className="mx-1.5 text-gold-400">•</span> Become
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <h2 className="text-2xl md:text-3xl">{passport.learner.display_name}</h2>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-forest-700 px-3 py-1 text-xs font-medium text-cream-50">
              <span className="h-1.5 w-1.5 rounded-full bg-gold-400" />
              {STATUS_LABEL[passport.status]}
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
                {passport.insight_source === "AI" ? "AI-assisted headline" : "Signal-based headline"} · evolves
                with new evidence
              </p>
            </>
          )}
        </div>

        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 border-cream-200 text-sm md:col-span-2 lg:col-span-1 lg:grid-cols-1 lg:border-l lg:pl-8">
          <Fact label="Passport no." value={passport.passport_number} />
          <Fact label="Member since" value={formatDate(passport.learner.member_since)} />
          <Fact label="Last updated" value={formatDate(passport.updated_at)} />
          <Fact label="Journey stage" value={currentStage} />
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

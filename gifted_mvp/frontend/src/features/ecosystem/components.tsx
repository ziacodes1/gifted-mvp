import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import type { CircleCard, Match, OpportunityCard, Organization, ResourceCard, ResourceType } from "../../types/ecosystem";
import { ArrowIcon, CheckIcon, ClockIcon, SparkIcon } from "../passport/icons";
import { coverFor } from "./covers";
import { TYPE_ICON } from "./hooks";
import { BookmarkIcon, CircleIcon, MonitorIcon, PeopleIcon, PinIcon, PlayIcon } from "./icons";
import { ageText, deadlineText, durationText, locationText, reasonText, resourceCta } from "./lib";

const LEVEL_STYLE: Record<string, string> = {
  STRONG_FIT: "bg-gold-50 text-gold-600 ring-gold-400/40",
  WORTH_EXPLORING: "bg-forest-50 text-forest-700 ring-forest-700/15",
  NEW_AREA: "bg-cream-100 text-forest-700 ring-cream-200",
};

/** "Strong fit" / "Worth exploring" / "New area to try". Never a percentage. */
export function MatchBadge({ match, className = "" }: { match: Match; className?: string }) {
  const { t } = useTranslation();
  if (match.level === "EXPLORE") return null;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ${LEVEL_STYLE[match.level]} ${className}`}>
      {match.level === "STRONG_FIT" && <SparkIcon className="h-3 w-3" />}
      {t(`eco.match.${match.level}`)}
    </span>
  );
}

/** Transparent reasons, or an honest "suggested exploration" note when the Passport is empty. */
export function WhyThisMatches({ match, title }: { match: Match; title?: string }) {
  const { t } = useTranslation();
  if (match.level === "EXPLORE") {
    return (
      <div className="rounded-2xl border border-cream-200 bg-cream-50 p-5">
        <p className="font-serif text-lg text-forest-800">{t("eco.why.suggested")}</p>
        <p className="mt-1 text-sm leading-relaxed text-sage-600">{t("eco.why.noSignals")}</p>
        <Link to="/app/assessment" className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-forest-700 hover:underline">
          {t("eco.why.takeAssessment")} <ArrowIcon />
        </Link>
      </div>
    );
  }
  return (
    <div className="rounded-2xl border border-cream-200 bg-white p-5">
      <div className="flex flex-wrap items-center gap-2">
        <p className="font-serif text-lg text-forest-800">{title ?? t("eco.why.title")}</p>
        <MatchBadge match={match} />
      </div>
      <ul className="mt-3 space-y-2">
        {match.reasons.map((r, i) => (
          <li key={i} className="flex items-start gap-2 text-sm leading-relaxed text-forest-700">
            <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-forest-700 text-cream-50">
              <CheckIcon className="h-3 w-3" />
            </span>
            {reasonText(t, r)}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-sage-600">{t("eco.why.note")}</p>
    </div>
  );
}

export function DemoPill({ org }: { org: Organization }) {
  const { t } = useTranslation();
  if (!org.is_demo) return null;
  return (
    <span className="rounded-full border border-dashed border-sage-400 bg-white/80 px-2 py-0.5 text-[11px] font-medium text-sage-600" title={t("eco.demo.orgNote")}>
      {t("eco.demo.pill")}
    </span>
  );
}

export function ProviderLine({ org, className = "" }: { org: Organization; className?: string }) {
  const { t } = useTranslation();
  return (
    <p className={`flex flex-wrap items-center gap-1.5 text-xs text-sage-600 ${className}`}>
      <span>{t("eco.providedBy", { name: org.name })}</span>
      {org.verified && <span className="text-forest-700">· {t("eco.verified")}</span>}
      <DemoPill org={org} />
    </p>
  );
}

export function Chip({ children, tone = "sage" }: { children: ReactNode; tone?: "sage" | "gold" | "cream" }) {
  const tones = { sage: "bg-forest-50 text-forest-700", gold: "bg-gold-50 text-gold-600", cream: "bg-cream-100 text-sage-600" };
  return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}>{children}</span>;
}

const TYPE_TONE: Record<ResourceType, string> = {
  ARTICLE: "bg-forest-50 text-forest-700",
  VIDEO: "bg-gold-50 text-gold-600",
  TOOLKIT: "bg-[#E8EEF7] text-[#35507A]",
  COURSE: "bg-[#EFE9F6] text-[#5B477A]",
};

export function SaveButton({ saved, onToggle, busy, label }: { saved: boolean; onToggle: () => void; busy?: boolean; label: string }) {
  const { t } = useTranslation();
  return (
    <button
      type="button"
      onClick={onToggle}
      disabled={busy}
      aria-pressed={saved}
      aria-label={saved ? t("eco.unsave", { title: label }) : t("eco.save", { title: label })}
      className={`grid h-9 w-9 place-items-center rounded-full transition hover:bg-forest-50 disabled:opacity-50 ${saved ? "text-gold-600" : "text-forest-700"}`}
    >
      <BookmarkIcon filled={saved} />
    </button>
  );
}

export function ResourceTile({ r, onToggleSave, busy }: { r: ResourceCard; onToggleSave?: () => void; busy?: boolean }) {
  const { t } = useTranslation();
  const Icon = TYPE_ICON[r.type];
  return (
    <article className="flex flex-col overflow-hidden rounded-2xl border border-cream-200/80 bg-white shadow-card">
      <Link to={`/app/resources/${r.slug}`} className="relative block">
        <img src={coverFor(r.cover_key)} alt="" className="h-36 w-full object-cover" loading="lazy" />
        {r.type === "VIDEO" && (
          <span className="absolute inset-0 grid place-items-center">
            <span className="grid h-11 w-11 place-items-center rounded-full bg-black/40 text-white ring-2 ring-white/80">
              <PlayIcon className="h-5 w-5" />
            </span>
          </span>
        )}
      </Link>
      <div className="flex flex-1 flex-col p-4">
        <div className="flex items-center justify-between gap-2">
          <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${TYPE_TONE[r.type]}`}>
            <Icon className="h-3.5 w-3.5" /> {t(`eco.resources.type.${r.type}`)}
          </span>
          <span className="inline-flex items-center gap-1 text-xs text-sage-600">
            <ClockIcon className="h-3.5 w-3.5" /> {durationText(t, r.duration_minutes)}
          </span>
        </div>
        <Link to={`/app/resources/${r.slug}`} className="mt-2.5 font-serif text-lg leading-snug text-forest-800 hover:underline">
          {r.title}
        </Link>
        <p className="mt-1 line-clamp-3 text-sm leading-relaxed text-sage-600">{r.short_description}</p>
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          <MatchBadge match={r.match} />
          {r.status === "COMPLETED" && <Chip>{t("eco.resources.status.COMPLETED")}</Chip>}
          {r.status === "IN_PROGRESS" && <Chip tone="gold">{t("eco.resources.status.IN_PROGRESS")}</Chip>}
        </div>
        <ProviderLine org={r.organization} className="mt-2" />
        <div className="mt-auto flex items-center justify-between pt-3">
          <Link to={`/app/resources/${r.slug}`} className="inline-flex items-center gap-1.5 text-sm font-medium text-forest-700 hover:underline">
            {resourceCta(t, r.type, r.status === "IN_PROGRESS")} <ArrowIcon />
          </Link>
          {onToggleSave && <SaveButton saved={r.saved} onToggle={onToggleSave} busy={busy} label={r.title} />}
        </div>
      </div>
    </article>
  );
}

export function OpportunityTile({ o, onToggleSave, busy }: { o: OpportunityCard; onToggleSave?: () => void; busy?: boolean }) {
  const { t, i18n } = useTranslation();
  const closed = o.eligibility.deadline.status === "CLOSED";
  return (
    <article className={`flex flex-col overflow-hidden rounded-2xl border border-cream-200/80 bg-white shadow-card ${closed ? "opacity-75" : ""}`}>
      <Link to={`/app/opportunities/${o.slug}`} className="relative block">
        <img src={coverFor(o.cover_key)} alt="" className="h-36 w-full object-cover" loading="lazy" />
        {o.match.level === "STRONG_FIT" && (
          <span className="absolute left-3 top-3 rounded-lg bg-gold-400 px-2.5 py-1 text-xs font-semibold text-forest-900 shadow">
            {t("eco.match.STRONG_FIT")}
          </span>
        )}
      </Link>
      <div className="flex flex-1 flex-col p-4">
        <div className="flex flex-wrap gap-1.5">
          <Chip>{t(`eco.category.${o.category}`)}</Chip>
          <Chip tone="cream">{t(`eco.opportunities.type.${o.type}`)}</Chip>
        </div>
        <Link to={`/app/opportunities/${o.slug}`} className="mt-2.5 font-serif text-lg leading-snug text-forest-800 hover:underline">
          {o.title}
        </Link>
        <p className="mt-0.5 text-xs text-sage-600">{o.organization.name}</p>
        <p className="mt-1.5 line-clamp-3 text-sm leading-relaxed text-sage-600">{o.short_description}</p>
        <div className="mt-3 grid gap-1 text-xs text-forest-700">
          <span className="inline-flex items-center gap-1.5">
            <PeopleIcon className="h-3.5 w-3.5" /> {ageText(t, o.age_min, o.age_max)}
          </span>
          <span className="inline-flex items-center gap-1.5">
            {o.mode === "ONLINE" ? <MonitorIcon className="h-3.5 w-3.5" /> : <PinIcon className="h-3.5 w-3.5" />} {locationText(t, o)}
          </span>
          <span className={`inline-flex items-center gap-1.5 ${o.eligibility.deadline.status === "CLOSING_SOON" ? "font-medium text-gold-600" : ""}`}>
            <ClockIcon className="h-3.5 w-3.5" /> {deadlineText(t, o.eligibility, o.application_deadline, i18n.language)}
          </span>
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          {o.match.level !== "STRONG_FIT" && <MatchBadge match={o.match} />}
          <DemoPill org={o.organization} />
        </div>
        <div className="mt-auto flex items-center justify-between pt-3">
          <Link to={`/app/opportunities/${o.slug}`} className="inline-flex items-center gap-1.5 text-sm font-medium text-forest-700 hover:underline">
            {t("eco.opportunities.viewDetails")} <ArrowIcon />
          </Link>
          {onToggleSave && <SaveButton saved={o.saved} onToggle={onToggleSave} busy={busy} label={o.title} />}
        </div>
      </div>
    </article>
  );
}

export function CircleTile({ c, onJoin, busy, compact }: { c: CircleCard; onJoin?: () => void; busy?: boolean; compact?: boolean }) {
  const { t } = useTranslation();
  return (
    <article className="flex flex-col overflow-hidden rounded-2xl border border-cream-200/80 bg-white shadow-card">
      <div className="relative">
        <img src={coverFor(c.cover_key)} alt="" className={`${compact ? "h-24" : "h-32"} w-full object-cover`} loading="lazy" />
        <span className="absolute -bottom-6 left-4 grid h-12 w-12 place-items-center rounded-full bg-white text-gold-600 shadow-card">
          <CircleIcon name={c.icon_key} />
        </span>
      </div>
      <div className="flex flex-1 flex-col p-4 pt-8">
        <h3 className="font-serif text-lg leading-snug text-forest-800">{c.name}</h3>
        <p className="mt-1 line-clamp-3 text-sm leading-relaxed text-sage-600">{c.description}</p>
        {c.reason && <p className="mt-2 text-xs font-medium text-gold-600">{t(`eco.community.reason.${c.reason.code}`, { label: c.reason.label })}</p>}
        <div className="mt-auto flex items-center justify-between gap-2 pt-3">
          <span className="text-xs text-sage-600">{t("eco.community.members", { count: c.member_count })}</span>
          {onJoin &&
            (c.joined ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-forest-50 px-3 py-1.5 text-xs font-medium text-forest-700">
                <CheckIcon className="h-3.5 w-3.5" /> {t("eco.community.joined")}
              </span>
            ) : (
              <button type="button" onClick={onJoin} disabled={busy} className="rounded-full bg-forest-50 px-4 py-1.5 text-sm font-medium text-forest-700 transition hover:bg-forest-700 hover:text-cream-50 disabled:opacity-50">
                {t("eco.community.join")}
              </button>
            ))}
        </div>
      </div>
    </article>
  );
}

export function SectionTitle({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="text-2xl">{title}</h2>
        {subtitle && <p className="mt-0.5 text-sm text-sage-600">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function LoadError({ onRetry }: { onRetry: () => void }) {
  const { t } = useTranslation();
  return (
    <div className="mx-auto max-w-3xl card text-center">
      <p className="text-sage-600">{t("eco.loadError")}</p>
      <button onClick={onRetry} className="btn-ghost mt-3">
        {t("common.retry")}
      </button>
    </div>
  );
}

export function PageSkeleton() {
  return (
    <div className="mx-auto max-w-6xl space-y-6" aria-busy>
      <div className="h-64 animate-pulse rounded-3xl bg-white" />
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-72 animate-pulse rounded-2xl bg-white" />
        ))}
      </div>
    </div>
  );
}

import { useQuery } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { ecosystemApi } from "../../api/ecosystem";
import type { MissionSummary } from "../../types/mission";
import { ArrowIcon, CompassIcon } from "../passport/icons";
import { MatchBadge } from "./components";
import { coverFor } from "./covers";
import { BriefcaseIcon, OpenBookIcon, PeopleIcon } from "./icons";
import { deadlineText, durationText, ECO_KEYS } from "./lib";

function MiniCard({ to, label, icon, image, title, meta, badge }: { to: string; label: string; icon: ReactNode; image?: string; title: string; meta: string; badge?: ReactNode }) {
  return (
    <Link to={to} className="group flex gap-3 rounded-2xl border border-cream-200/80 bg-white p-3 transition hover:shadow-card">
      {image ? (
        <img src={image} alt="" className="h-20 w-20 shrink-0 rounded-xl object-cover" loading="lazy" />
      ) : (
        <span className="grid h-20 w-20 shrink-0 place-items-center rounded-xl bg-forest-50 text-forest-700">{icon}</span>
      )}
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-1.5 text-xs font-medium text-gold-600">
          {icon} {label}
        </span>
        <span className="mt-0.5 line-clamp-2 block font-serif text-base leading-snug text-forest-800 group-hover:underline">{title}</span>
        <span className="mt-1 flex flex-wrap items-center gap-1.5 text-xs text-sage-600">
          {meta} {badge}
        </span>
      </span>
    </Link>
  );
}

function useForYou() {
  return useQuery({ queryKey: ECO_KEYS.forYou, queryFn: ecosystemApi.forYou, staleTime: 60_000 });
}

/** Home: one resource, one opportunity and one circle — after the core Passport/next-step content. */
export function EcosystemHomeCard() {
  const { t, i18n } = useTranslation();
  const { data, isError } = useForYou();
  if (isError) return null; // ecosystem suggestions never block Home
  if (!data) return <div className="h-36 animate-pulse rounded-2xl bg-white shadow-card" />;
  if (!data.resource && !data.opportunity && !data.circle) return null;

  return (
    <section className="card" aria-label={t("eco.home.title")}>
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-xl">{t("eco.home.title")}</h2>
          <p className="text-sm text-sage-600">{data.has_signals ? t("eco.home.subtitle") : t("eco.home.subtitleNoSignals")}</p>
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {data.resource && (
          <MiniCard
            to={`/app/resources/${data.resource.slug}`}
            label={t("eco.home.resource")}
            icon={<OpenBookIcon className="h-3.5 w-3.5" />}
            image={coverFor(data.resource.cover_key)}
            title={data.resource.title}
            meta={`${t(`eco.resources.type.${data.resource.type}`)} · ${durationText(t, data.resource.duration_minutes)}`}
            badge={<MatchBadge match={data.resource.match} />}
          />
        )}
        {data.opportunity && (
          <MiniCard
            to={`/app/opportunities/${data.opportunity.slug}`}
            label={t("eco.home.opportunity")}
            icon={<BriefcaseIcon className="h-3.5 w-3.5" />}
            image={coverFor(data.opportunity.cover_key)}
            title={data.opportunity.title}
            meta={deadlineText(t, data.opportunity.eligibility, data.opportunity.application_deadline, i18n.language)}
            badge={<MatchBadge match={data.opportunity.match} />}
          />
        )}
        {data.circle && (
          <MiniCard
            to="/app/community"
            label={t("eco.home.circle")}
            icon={<PeopleIcon className="h-3.5 w-3.5" />}
            image={coverFor(data.circle.cover_key)}
            title={data.circle.name}
            meta={t("eco.community.members", { count: data.circle.member_count })}
          />
        )}
      </div>
    </section>
  );
}

/** Passport: "Explore next" — mission, resource and opportunity side by side. Adds nothing to the
 * Passport's own structure; it only links onward. */
export function ExploreNext({ mission }: { mission: MissionSummary | null }) {
  const { t, i18n } = useTranslation();
  const { data } = useForYou();
  const showMission = mission && mission.my_attempt?.status !== "COMPLETED";
  if (!showMission && !data?.resource && !data?.opportunity) return null;

  return (
    <section className="space-y-3" aria-label={t("eco.passport.title")}>
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h2 className="text-2xl">{t("eco.passport.title")}</h2>
          <p className="text-sm text-sage-600">{t("eco.passport.note")}</p>
        </div>
        <Link to="/app/opportunities" className="inline-flex items-center gap-1.5 text-sm font-medium text-forest-700 hover:underline">
          {t("eco.passport.more")} <ArrowIcon />
        </Link>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        {showMission && (
          <MiniCard
            to={`/app/missions/${mission.slug}`}
            label={t("eco.passport.mission")}
            icon={<CompassIcon className="h-3.5 w-3.5" />}
            title={mission.title}
            meta={mission.time_label}
          />
        )}
        {data?.resource && (
          <MiniCard
            to={`/app/resources/${data.resource.slug}`}
            label={t("eco.home.resource")}
            icon={<OpenBookIcon className="h-3.5 w-3.5" />}
            image={coverFor(data.resource.cover_key)}
            title={data.resource.title}
            meta={durationText(t, data.resource.duration_minutes)}
            badge={<MatchBadge match={data.resource.match} />}
          />
        )}
        {data?.opportunity && (
          <MiniCard
            to={`/app/opportunities/${data.opportunity.slug}`}
            label={t("eco.home.opportunity")}
            icon={<BriefcaseIcon className="h-3.5 w-3.5" />}
            image={coverFor(data.opportunity.cover_key)}
            title={data.opportunity.title}
            meta={deadlineText(t, data.opportunity.eligibility, data.opportunity.application_deadline, i18n.language)}
            badge={<MatchBadge match={data.opportunity.match} />}
          />
        )}
      </div>
    </section>
  );
}

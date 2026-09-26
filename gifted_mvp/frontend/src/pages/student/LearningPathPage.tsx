import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { ecosystemApi } from "../../api/ecosystem";
import { LoadError, MatchBadge, PageSkeleton, ProviderLine } from "../../features/ecosystem/components";
import { coverFor } from "../../features/ecosystem/covers";
import { TYPE_ICON } from "../../features/ecosystem/hooks";
import { LayersIcon } from "../../features/ecosystem/icons";
import { durationText, ECO_KEYS } from "../../features/ecosystem/lib";
import { ArrowIcon, BackIcon, CheckIcon, ClockIcon } from "../../features/passport/icons";

/** /app/resources/paths/:slug — an ordered group of resources with simple progress (not an LMS). */
export function LearningPathPage() {
  const { slug = "" } = useParams();
  const { t } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ECO_KEYS.path(slug), queryFn: () => ecosystemApi.path(slug) });

  if (isLoading) return <PageSkeleton />;
  if (isError || !data) return <LoadError onRetry={() => void refetch()} />;
  const items = data.items ?? [];
  const pct = data.resource_count ? Math.round((data.completed_count / data.resource_count) * 100) : 0;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <Link to="/app/resources" className="inline-flex items-center gap-1.5 text-sm text-forest-700 hover:underline">
        <BackIcon /> {t("eco.resources.back")}
      </Link>
      <header className="relative overflow-hidden rounded-3xl border border-cream-200/80 shadow-card">
        <img src={coverFor(data.cover_key)} alt="" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-cream-50 via-cream-50/90 to-cream-50/20" />
        <div className="relative max-w-xl p-7 md:p-9">
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-600">{t("eco.resources.path.label")}</p>
          <h1 className="mt-2 text-3xl leading-tight md:text-4xl">{data.title}</h1>
          <p className="mt-2 leading-relaxed text-forest-700">{data.description}</p>
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-sm text-forest-700">
            <span className="inline-flex items-center gap-1.5">
              <LayersIcon /> {t("eco.resources.path.count", { count: data.resource_count })}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <ClockIcon /> {durationText(t, data.duration_minutes)}
            </span>
            <span>{t(`eco.difficulty.${data.difficulty}`)}</span>
          </div>
          <ProviderLine org={data.organization} className="mt-3" />
          <div className="mt-4 max-w-sm">
            <div className="h-2 overflow-hidden rounded-full bg-white/80" role="progressbar" aria-valuenow={data.completed_count} aria-valuemin={0} aria-valuemax={data.resource_count}>
              <div className="h-full rounded-full bg-forest-700 transition-all" style={{ width: `${pct}%` }} />
            </div>
            <p className="mt-1.5 text-xs text-forest-700">{t("eco.resources.path.progress", { done: data.completed_count, total: data.resource_count })}</p>
          </div>
          {data.next_resource && (
            <Link to={`/app/resources/${data.next_resource}`} className="btn-primary mt-5 gap-2">
              {data.completed_count ? t("eco.resources.path.continue") : t("eco.resources.path.start")} <ArrowIcon />
            </Link>
          )}
          {!data.next_resource && <p className="mt-5 font-serif text-lg text-forest-800">{t("eco.resources.path.done")}</p>}
        </div>
      </header>

      <ol className="space-y-3">
        {items.map((r, i) => {
          const Icon = TYPE_ICON[r.type];
          const done = r.status === "COMPLETED";
          return (
            <li key={r.slug}>
              <Link to={`/app/resources/${r.slug}`} className="flex items-center gap-4 rounded-2xl border border-cream-200/80 bg-white p-4 shadow-soft transition hover:shadow-card">
                <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-sm font-semibold ${done ? "bg-forest-700 text-cream-50" : "bg-forest-50 text-forest-700"}`}>
                  {done ? <CheckIcon /> : i + 1}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-center gap-2 text-xs text-sage-600">
                    <Icon className="h-3.5 w-3.5" /> {t(`eco.resources.type.${r.type}`)} · {durationText(t, r.duration_minutes)}
                    <MatchBadge match={r.match} />
                  </span>
                  <span className="mt-0.5 block font-serif text-lg leading-snug text-forest-800">{r.title}</span>
                </span>
                <ArrowIcon />
              </Link>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

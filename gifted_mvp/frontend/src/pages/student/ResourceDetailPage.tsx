import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { ecosystemApi } from "../../api/ecosystem";
import { Chip, LoadError, PageSkeleton, ProviderLine, SaveButton, WhyThisMatches } from "../../features/ecosystem/components";
import { coverFor } from "../../features/ecosystem/covers";
import { TYPE_ICON } from "../../features/ecosystem/hooks";
import { ExternalIcon, LayersIcon } from "../../features/ecosystem/icons";
import { durationText, ECO_KEYS } from "../../features/ecosystem/lib";
import { ArrowIcon, BackIcon, BulbIcon, CheckIcon, ClockIcon, LeafIcon } from "../../features/passport/icons";
import type { ResourceAction, ResourceDetail } from "../../types/ecosystem";

/** /app/resources/:slug — content (or the provider's link), progress and "why this fits you". */
export function ResourceDetailPage() {
  const { slug = "" } = useParams();
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ECO_KEYS.resource(slug), queryFn: () => ecosystemApi.resource(slug) });
  const act = useMutation({
    mutationFn: (action: ResourceAction) => ecosystemApi.resourceAction(slug, action),
    onSuccess: (detail) => {
      qc.setQueryData(ECO_KEYS.resource(slug), detail);
      void qc.invalidateQueries({ queryKey: ["eco"], predicate: (q) => q.queryKey[1] !== "resource" });
    },
  });

  if (isLoading) return <PageSkeleton />;
  if (isError || !data) return <LoadError onRetry={() => void refetch()} />;
  const Icon = TYPE_ICON[data.type];

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <Link to="/app/resources" className="inline-flex items-center gap-1.5 text-sm text-forest-700 hover:underline">
        <BackIcon /> {t("eco.resources.back")}
      </Link>

      <header className="overflow-hidden rounded-3xl border border-cream-200/80 bg-white shadow-card md:grid md:grid-cols-[1fr_0.9fr]">
        <div className="p-7 md:p-9">
          <div className="flex flex-wrap items-center gap-2">
            <Chip>
              <Icon className="mr-1 h-3.5 w-3.5" /> {t(`eco.resources.type.${data.type}`)}
            </Chip>
            <Chip tone="cream">{t(`eco.category.${data.category}`)}</Chip>
            {data.status !== "NOT_STARTED" && <Chip tone="gold">{t(`eco.resources.status.${data.status}`)}</Chip>}
          </div>
          <h1 className="mt-3 text-3xl leading-tight md:text-4xl">{data.title}</h1>
          <p className="mt-2 leading-relaxed text-sage-600">{data.short_description}</p>
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-1 text-sm text-forest-700">
            <span className="inline-flex items-center gap-1.5">
              <ClockIcon /> {durationText(t, data.duration_minutes)}
            </span>
            <span>{t(`eco.difficulty.${data.difficulty}`)}</span>
          </div>
          <ProviderLine org={data.organization} className="mt-3" />
          <div className="mt-5 flex flex-wrap items-center gap-2">
            <ProgressActions data={data} busy={act.isPending} onAction={(a) => act.mutate(a)} />
            <SaveButton saved={data.saved} onToggle={() => act.mutate(data.saved ? "unsave" : "save")} busy={act.isPending} label={data.title} />
          </div>
          {act.isError && <p className="mt-2 text-sm text-red-700">{t("eco.actionError")}</p>}
        </div>
        <img src={coverFor(data.cover_key)} alt="" className="h-56 w-full object-cover md:h-full" />
      </header>

      <div className="grid items-start gap-6 lg:grid-cols-[1.4fr_1fr]">
        <article className="card space-y-5">
          {data.is_external ? (
            <div className="rounded-2xl bg-cream-50 p-5">
              <p className="text-sm leading-relaxed text-forest-700">{t("eco.resources.externalNote", { name: data.organization.name })}</p>
              <a
                href={data.external_url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={() => act.mutate("open")}
                className="btn-primary mt-3 gap-2"
              >
                {t("eco.resources.openResource")} <ExternalIcon />
              </a>
              {data.organization.website_url && (
                <a href={data.organization.website_url} target="_blank" rel="noopener noreferrer" className="ml-2 mt-3 inline-flex items-center gap-1.5 text-sm text-forest-700 hover:underline">
                  {t("eco.resources.visitProvider")} <ExternalIcon />
                </a>
              )}
            </div>
          ) : (
            <p className="rounded-xl border border-dashed border-sage-400 bg-cream-50 px-4 py-2.5 text-xs leading-relaxed text-sage-600">
              {data.organization.is_demo ? t("eco.demo.curated") : t("eco.resources.inGifted")}
            </p>
          )}
          {data.content.intro && <p className="text-lg leading-relaxed text-forest-800">{data.content.intro}</p>}
          {!!data.content.points?.length && (
            <div>
              <h2 className="text-xl">{data.type === "COURSE" ? t("eco.resources.lessons") : t("eco.resources.keyIdeas")}</h2>
              <ol className="mt-3 space-y-2.5">
                {data.content.points.map((p, i) => (
                  <li key={i} className="flex gap-3 text-forest-700">
                    <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-forest-50 text-xs font-semibold text-forest-700">{i + 1}</span>
                    <span className="leading-relaxed">{p}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}
          {data.content.try_this && (
            <div className="flex gap-3 rounded-2xl bg-gold-50 p-4">
              <BulbIcon className="h-5 w-5 shrink-0 text-gold-600" />
              <div>
                <p className="text-sm font-semibold text-forest-800">{t("eco.resources.tryThis")}</p>
                <p className="mt-0.5 text-sm leading-relaxed text-forest-700">{data.content.try_this}</p>
              </div>
            </div>
          )}
        </article>

        <aside className="space-y-4">
          <WhyThisMatches match={data.match} />
          {data.produces_evidence && (
            <div className="flex gap-3 rounded-2xl border border-cream-200 bg-white p-4 text-sm leading-relaxed text-forest-700">
              <LeafIcon className="h-5 w-5 shrink-0 text-forest-700" />
              {data.evidence_recorded ? t("eco.resources.evidenceRecorded") : t("eco.resources.evidenceNote")}
            </div>
          )}
          {data.paths.map((p) => (
            <Link key={p.slug} to={`/app/resources/paths/${p.slug}`} className="flex items-center gap-3 rounded-2xl border border-cream-200 bg-white p-4 text-sm text-forest-700 transition hover:shadow-soft">
              <LayersIcon className="h-5 w-5 text-gold-600" />
              <span className="flex-1">
                <span className="block text-xs text-sage-600">{t("eco.resources.partOfPath")}</span>
                {p.title}
              </span>
              <ArrowIcon />
            </Link>
          ))}
        </aside>
      </div>
    </div>
  );
}

function ProgressActions({ data, busy, onAction }: { data: ResourceDetail; busy: boolean; onAction: (a: ResourceAction) => void }) {
  const { t } = useTranslation();
  if (data.status === "COMPLETED") {
    return (
      <>
        <span className="inline-flex items-center gap-1.5 rounded-full bg-forest-50 px-4 py-2 text-sm font-medium text-forest-700">
          <CheckIcon /> {t("eco.resources.status.COMPLETED")}
        </span>
        <button type="button" onClick={() => onAction("reset")} disabled={busy} className="text-xs text-sage-600 underline-offset-2 hover:underline">
          {t("eco.resources.undo")}
        </button>
      </>
    );
  }
  if (data.tracks_progress && data.status === "NOT_STARTED") {
    return (
      <button type="button" onClick={() => onAction("start")} disabled={busy} className="btn-primary">
        {t("eco.resources.startCourse")}
      </button>
    );
  }
  return (
    <button type="button" onClick={() => onAction("complete")} disabled={busy} className="btn-primary gap-2">
      <CheckIcon /> {t("eco.resources.markComplete")}
    </button>
  );
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { todayApi } from "../../api/today";
import type { SparkAction } from "../../types/today";
import { BookIcon, CheckIcon, SparkIcon } from "../passport/icons";
import { ENGAGEMENT_KEY } from "../rewards/lib";
import { TODAY_KEY, sparkHref, sparkTitle } from "./sparkText";

/** Home: one light, personal card per day (deterministic backend pick; no AI call). */
export function TodaySpark() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: TODAY_KEY, queryFn: todayApi.get, staleTime: 60_000 });
  const act = useMutation({
    mutationFn: (action: "complete" | "dismiss" | "restore") => todayApi.act(data!.spark.key, action),
    onSuccess: (next, action) => {
      qc.setQueryData(TODAY_KEY, next);
      if (action === "complete") void qc.invalidateQueries({ queryKey: ENGAGEMENT_KEY });
    },
  });

  if (isLoading) return <div className="h-44 animate-pulse rounded-3xl bg-white shadow-card" />;
  if (!data) return null; // no spark today (e.g. offline) — Home works without it
  const { spark } = data;
  const motivation = t(`sparks.motivation.${data.motivation}`, { defaultValue: "" });

  if (spark.status === "DISMISSED") {
    return (
      <section aria-label={t("sparks.title")} className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-dashed border-cream-200 bg-cream-50 px-5 py-3 text-sm text-sage-600">
        <span className="inline-flex items-center gap-2">
          <SparkIcon className="h-4 w-4 text-gold-500" /> {t("sparks.dismissed")} {t("sparks.tomorrow")}
        </span>
        <button onClick={() => act.mutate("restore")} disabled={act.isPending} className="font-medium text-forest-700 hover:underline">
          {t("sparks.actions.restore")}
        </button>
      </section>
    );
  }

  const done = spark.status === "DONE";
  // State-driven sparks carry their own button text; reflections use the generic actions.
  const label = (a: SparkAction) =>
    a === "go" || spark.route === a ? t(`sparks.items.${spark.key}.cta`, { defaultValue: t(`sparks.actions.${a}`) }) : t(`sparks.actions.${a}`);

  return (
    <section
      aria-label={t("sparks.title")}
      data-testid="today-spark"
      className="relative overflow-hidden rounded-3xl border border-gold-400/40 bg-gradient-to-br from-[#FFF8EC] via-white to-forest-50/40 p-6 shadow-card md:p-7"
    >
      <SparkArt className="pointer-events-none absolute -bottom-16 -right-10 h-40 w-40 opacity-40" />
      <div className="relative flex flex-col gap-5 md:flex-row md:items-center">
        <div className="min-w-0 flex-1">
          <p className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[0.25em] text-gold-600">
            <SparkIcon className="h-4 w-4" /> {t("sparks.title")}
            <span className="rounded-full bg-white/80 px-2 py-0.5 text-[10px] font-medium normal-case tracking-normal text-forest-700 ring-1 ring-cream-200">
              {t(`sparks.types.${spark.type}`)}
            </span>
          </p>
          <h2 className="mt-3 max-w-2xl text-2xl leading-snug md:text-[1.7rem]" data-testid="spark-title">
            {sparkTitle(t, spark.key)}
          </h2>
          {spark.type !== "FACT" && <p className="mt-2 max-w-2xl text-sm leading-relaxed text-forest-700/85">{t(`sparks.items.${spark.key}.body`, { defaultValue: "" })}</p>}
          {motivation && <p className="mt-3 font-hand text-xl text-forest-700">{motivation}</p>}
        </div>

        <div className="flex shrink-0 flex-col items-start gap-2 md:items-end">
          {done ? (
            <p role="status" className="inline-flex flex-wrap items-center gap-x-2 gap-y-0.5 rounded-2xl bg-forest-700 px-4 py-2 text-sm font-medium text-cream-50">
              <CheckIcon /> {t("sparks.done")}
              {spark.points > 0 && <span className="whitespace-nowrap text-gold-400">+{t("rewards.points.value", { count: spark.points })}</span>}
            </p>
          ) : (
            spark.actions.map((a, i) => {
              if (a === "complete") {
                return (
                  <button key={a} onClick={() => act.mutate("complete")} disabled={act.isPending} className="btn-primary gap-2 px-5 py-2.5">
                    <CheckIcon /> {t("sparks.actions.complete")}
                    <span className="text-gold-400">+{spark.points}</span>
                  </button>
                );
              }
              const href = sparkHref(spark, a);
              return (
                href && (
                  <Link key={a} to={href} className={`${i === 0 ? "btn-primary" : "btn-ghost bg-white"} gap-2 px-5 py-2.5`}>
                    {a === "diary" ? <BookIcon className="h-4 w-4" /> : <SparkIcon className="h-4 w-4" />} {label(a)}
                  </Link>
                )
              );
            })
          )}
          {done ? (
            <p className="text-xs text-sage-600">{t("sparks.tomorrow")}</p>
          ) : (
            <button onClick={() => act.mutate("dismiss")} disabled={act.isPending} className="px-1 text-xs text-sage-600 hover:text-forest-700 hover:underline">
              {t("sparks.actions.dismiss")}
            </button>
          )}
        </div>
      </div>
    </section>
  );
}

/** Soft sunburst + leaf, drawn in the Gifted palette. */
function SparkArt({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 160 160" className={className} aria-hidden>
      <circle cx="80" cy="80" r="46" fill="#F6E3B8" opacity="0.55" />
      {Array.from({ length: 12 }, (_, i) => (
        <path key={i} d="M80 18v16" stroke="#E0B85A" strokeWidth="3" strokeLinecap="round" opacity="0.55" transform={`rotate(${i * 30} 80 80)`} />
      ))}
      <path d="M62 104c0-24 14-38 38-40-2 24-15 38-38 40Z" fill="#7C9A6B" opacity="0.8" />
      <path d="M64 102 94 70" stroke="#FFFDF7" strokeWidth="2" opacity="0.7" />
    </svg>
  );
}

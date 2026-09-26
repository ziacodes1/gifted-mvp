import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { ecosystemApi, type ResourceFilters } from "../../api/ecosystem";
import hero from "../../assets/ecosystem/resources_hero.webp";
import { PhotoHero } from "../../components/PhotoHero";
import { LoadError, PageSkeleton, ProviderLine, ResourceTile, SectionTitle } from "../../features/ecosystem/components";
import { coverFor } from "../../features/ecosystem/covers";
import { CATEGORIES, useSaveResource } from "../../features/ecosystem/hooks";
import { BookmarkIcon, CapIcon, GridIcon, LayersIcon, PlayIcon, SearchIcon, StarIcon, WrenchIcon, ArticleIcon } from "../../features/ecosystem/icons";
import { durationText, ECO_KEYS } from "../../features/ecosystem/lib";
import { ArrowIcon, ChartIcon, ClockIcon } from "../../features/passport/icons";
import type { LearningPathSummary, ResourceCard } from "../../types/ecosystem";

const TABS = [
  { key: "", icon: GridIcon },
  { key: "ARTICLE", icon: ArticleIcon },
  { key: "VIDEO", icon: PlayIcon },
  { key: "TOOLKIT", icon: WrenchIcon },
  { key: "COURSE", icon: CapIcon },
] as const;

/** /app/resources — library with type tabs, featured learning path and deterministic "for you" order. */
export function ResourcesPage() {
  const { t } = useTranslation();
  const [filters, setFilters] = useState<ResourceFilters>({ sort: "relevant" });
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: [...ECO_KEYS.resources, filters],
    queryFn: () => ecosystemApi.resources(filters),
    placeholderData: keepPreviousData,
  });
  const save = useSaveResource();
  const set = (patch: Partial<ResourceFilters>) => setFilters((f) => ({ ...f, ...patch }));
  const filtered = Boolean(filters.type || filters.category || filters.q || filters.saved);

  if (isLoading) return <PageSkeleton />;
  if (isError || !data) return <LoadError onRetry={() => void refetch()} />;

  const recommended = data.has_signals && !filtered ? data.items.filter((r) => r.match.level === "STRONG_FIT" && r.status !== "COMPLETED").slice(0, 4) : [];
  const tile = (r: ResourceCard) => (
    <ResourceTile key={r.slug} r={r} onToggleSave={() => save.mutate(r)} busy={save.isPending && save.variables?.slug === r.slug} />
  );

  return (
    <div className="mx-auto max-w-6xl space-y-7">
      <PhotoHero image={hero} eyebrow={t("eco.resources.eyebrow")} title={t("eco.resources.title")}>
        <p className="mt-3 max-w-xl leading-relaxed text-forest-700">{t("eco.resources.subtitle")}</p>
        <p className="mt-4 font-hand text-2xl text-gold-600">{t("eco.resources.hand")}</p>
      </PhotoHero>

      <div className="flex flex-wrap items-center gap-2" role="tablist" aria-label={t("eco.resources.typesLabel")}>
        {TABS.map(({ key, icon: Icon }) => {
          const active = (filters.type ?? "") === key && !filters.saved;
          return (
            <button
              key={key || "all"}
              role="tab"
              aria-selected={active}
              onClick={() => set({ type: key || undefined, saved: false })}
              className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition ${
                active ? "border-forest-700 bg-forest-700 text-cream-50" : "border-cream-200 bg-white text-forest-700 hover:bg-forest-50"
              }`}
            >
              <Icon className="h-4 w-4" /> {t(`eco.resources.tabs.${key || "ALL"}`)}
            </button>
          );
        })}
        <button
          role="tab"
          aria-selected={Boolean(filters.saved)}
          onClick={() => set({ saved: !filters.saved, type: undefined })}
          className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition ${
            filters.saved ? "border-gold-500 bg-gold-50 text-gold-600" : "border-cream-200 bg-white text-forest-700 hover:bg-forest-50"
          }`}
        >
          <BookmarkIcon className="h-4 w-4" /> {t("eco.resources.tabs.SAVED")}
        </button>
      </div>

      <div className="grid gap-3 md:grid-cols-[1fr_auto_auto]">
        <label className="relative block">
          <span className="sr-only">{t("eco.resources.search")}</span>
          <SearchIcon className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-sage-600" />
          <input
            className="input pl-10"
            type="search"
            placeholder={t("eco.resources.search")}
            value={filters.q ?? ""}
            onChange={(e) => set({ q: e.target.value })}
            maxLength={100}
          />
        </label>
        <select className="input md:w-56" aria-label={t("eco.filters.category")} value={filters.category ?? ""} onChange={(e) => set({ category: e.target.value || undefined })}>
          <option value="">{t("eco.filters.allCategories")}</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {t(`eco.category.${c}`)}
            </option>
          ))}
        </select>
        <select className="input md:w-52" aria-label={t("eco.resources.sortBy")} value={filters.sort} onChange={(e) => set({ sort: e.target.value as ResourceFilters["sort"] })}>
          {(["relevant", "shortest", "newest"] as const).map((s) => (
            <option key={s} value={s}>
              {t("eco.resources.sortBy")}: {t(`eco.resources.sort.${s}`)}
            </option>
          ))}
        </select>
      </div>

      {data.featured_path && !filtered && <FeaturedPath path={data.featured_path} />}

      {recommended.length > 0 && (
        <section className="space-y-4">
          <SectionTitle title={t("eco.resources.recommended")} subtitle={t("eco.resources.recommendedNote")} />
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{recommended.map(tile)}</div>
        </section>
      )}

      <section className="space-y-4">
        <SectionTitle
          title={filters.saved ? t("eco.resources.savedTitle") : t("eco.resources.all")}
          subtitle={data.has_signals ? t("eco.resources.orderNote") : t("eco.resources.noSignalsNote")}
        />
        {data.items.length === 0 ? (
          <div className="card text-center text-sage-600">{filters.saved ? t("eco.resources.noSaved") : t("eco.resources.empty")}</div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{data.items.map(tile)}</div>
        )}
      </section>
    </div>
  );
}

function FeaturedPath({ path }: { path: LearningPathSummary }) {
  const { t } = useTranslation();
  const started = path.completed_count > 0;
  return (
    <section className="relative overflow-hidden rounded-3xl border border-cream-200/80 bg-white shadow-card">
      <img src={coverFor(path.cover_key)} alt="" className="absolute inset-y-0 right-0 hidden h-full w-1/2 object-cover md:block" />
      <div className="absolute inset-y-0 right-0 hidden w-1/2 bg-gradient-to-r from-white via-white/40 to-transparent md:block" />
      <div className="relative max-w-xl p-7 md:p-9">
        <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.25em] text-gold-600">
          <StarIcon className="h-4 w-4" /> {t("eco.resources.path.featured")}
        </p>
        <h2 className="mt-2 text-3xl leading-tight">{path.title}</h2>
        <p className="mt-2 leading-relaxed text-sage-600">{path.description}</p>
        <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-forest-700">
          <span className="inline-flex items-center gap-1.5">
            <LayersIcon /> {t("eco.resources.path.count", { count: path.resource_count })}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <ClockIcon /> {durationText(t, path.duration_minutes)}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <ChartIcon className="h-4 w-4" /> {t(`eco.difficulty.${path.difficulty}`)}
          </span>
        </div>
        {started && (
          <p className="mt-3 text-sm font-medium text-forest-700">
            {t("eco.resources.path.progress", { done: path.completed_count, total: path.resource_count })}
          </p>
        )}
        <ProviderLine org={path.organization} className="mt-3" />
        <Link to={`/app/resources/paths/${path.slug}`} className="btn-primary mt-5 gap-2">
          {started ? t("eco.resources.path.continue") : t("eco.resources.path.start")} <ArrowIcon />
        </Link>
      </div>
    </section>
  );
}

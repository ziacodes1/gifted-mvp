import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { ecosystemApi } from "../../api/ecosystem";
import hero from "../../assets/ecosystem/opportunity_microscope.webp";
import { PhotoHero } from "../../components/PhotoHero";
import { Chip, LoadError, MatchBadge, OpportunityTile, PageSkeleton, SectionTitle } from "../../features/ecosystem/components";
import { coverFor } from "../../features/ecosystem/covers";
import { useSaveOpportunity } from "../../features/ecosystem/hooks";
import { SearchIcon } from "../../features/ecosystem/icons";
import { ageText, deadlineText, ECO_KEYS, locationText, reasonText } from "../../features/ecosystem/lib";
import { ArrowIcon, CheckIcon, SparkIcon } from "../../features/passport/icons";
import type { OpportunityCard, OpportunityFilters, OpportunityType } from "../../types/ecosystem";

type Quick = "all" | "STEM" | "ARTS" | "LEADERSHIP" | "ONLINE" | "IN_PERSON" | "saved";
const QUICK: Quick[] = ["all", "STEM", "ARTS", "LEADERSHIP", "ONLINE", "IN_PERSON", "saved"];
const AGES = [12, 13, 14, 15, 16, 17, 18];

function quickToFilters(q: Quick): OpportunityFilters {
  if (q === "ONLINE" || q === "IN_PERSON") return { mode: q };
  if (q === "saved") return { saved: true };
  if (q === "all") return {};
  return { category: q };
}

/** /app/opportunities — catalog with filters; one personal pick when the Passport supports it. */
export function OpportunitiesPage() {
  const { t } = useTranslation();
  const [quick, setQuick] = useState<Quick>("all");
  const [extra, setExtra] = useState<OpportunityFilters>({});
  const filters = { ...quickToFilters(quick), ...extra };
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: [...ECO_KEYS.opportunities, filters],
    queryFn: () => ecosystemApi.opportunities(filters),
    placeholderData: keepPreviousData,
  });
  const save = useSaveOpportunity();
  const setExtraField = (patch: OpportunityFilters) => setExtra((f) => ({ ...f, ...patch }));
  const filtered = quick !== "all" || Object.values(extra).some((v) => v !== undefined && v !== "");

  if (isLoading) return <PageSkeleton />;
  if (isError || !data) return <LoadError onRetry={() => void refetch()} />;
  const featured = !filtered ? data.featured : null;
  const items = featured ? data.items.filter((o) => o.slug !== featured.slug) : data.items;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PhotoHero image={hero} eyebrow={t("eco.opportunities.eyebrow")} title={t("eco.opportunities.title")}>
        <p className="mt-3 max-w-xl leading-relaxed text-forest-700">{t("eco.opportunities.subtitle")}</p>
      </PhotoHero>

      <label className="relative block">
        <span className="sr-only">{t("eco.opportunities.search")}</span>
        <SearchIcon className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-sage-600" />
        <input
          className="input pl-10"
          type="search"
          placeholder={t("eco.opportunities.search")}
          value={extra.q ?? ""}
          onChange={(e) => setExtraField({ q: e.target.value })}
          maxLength={100}
        />
      </label>

      <div className="flex flex-wrap gap-2" role="group" aria-label={t("eco.filters.quick")}>
        {QUICK.map((q) => (
          <button
            key={q}
            aria-pressed={quick === q}
            onClick={() => setQuick(q)}
            className={`rounded-full border px-4 py-1.5 text-sm font-medium transition ${
              quick === q ? "border-forest-700 bg-forest-700 text-cream-50" : "border-cream-200 bg-white text-forest-700 hover:bg-forest-50"
            }`}
          >
            {t(`eco.opportunities.quick.${q}`)}
          </button>
        ))}
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <select className="input" aria-label={t("eco.filters.type")} value={extra.type ?? ""} onChange={(e) => setExtraField({ type: (e.target.value || undefined) as OpportunityType | undefined })}>
          <option value="">{t("eco.filters.allTypes")}</option>
          {data.facets.types.map((ty) => (
            <option key={ty} value={ty}>
              {t(`eco.opportunities.type.${ty}`)}
            </option>
          ))}
        </select>
        <select className="input" aria-label={t("eco.filters.age")} value={extra.age ?? ""} onChange={(e) => setExtraField({ age: e.target.value ? Number(e.target.value) : undefined })}>
          <option value="">{t("eco.filters.anyAge")}</option>
          {AGES.map((a) => (
            <option key={a} value={a}>
              {t("eco.filters.ageValue", { age: a })}
            </option>
          ))}
        </select>
        <select className="input" aria-label={t("eco.filters.country")} value={extra.country ?? ""} onChange={(e) => setExtraField({ country: e.target.value || undefined })}>
          <option value="">{t("eco.filters.anyCountry")}</option>
          {data.facets.countries.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
        <select
          className="input"
          aria-label={t("eco.filters.deadline")}
          value={extra.deadline ?? ""}
          onChange={(e) => setExtraField({ deadline: (e.target.value || undefined) as OpportunityFilters["deadline"] })}
        >
          <option value="">{t("eco.filters.openNow")}</option>
          <option value="closing_soon">{t("eco.filters.closingSoon")}</option>
          <option value="all">{t("eco.filters.includeClosed")}</option>
        </select>
      </div>

      {featured && <FeaturedOpportunity o={featured} personal={data.has_signals && featured.match.level === "STRONG_FIT"} />}

      <section className="space-y-4">
        <SectionTitle
          title={quick === "saved" ? t("eco.opportunities.savedTitle") : t("eco.opportunities.all")}
          subtitle={data.has_signals ? t("eco.opportunities.orderNote") : t("eco.opportunities.noSignalsNote")}
        />
        {items.length === 0 ? (
          <div className="card text-center text-sage-600">{quick === "saved" ? t("eco.opportunities.noSaved") : t("eco.opportunities.empty")}</div>
        ) : (
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {items.map((o) => (
              <OpportunityTile key={o.slug} o={o} onToggleSave={() => save.mutate(o)} busy={save.isPending && save.variables?.slug === o.slug} />
            ))}
          </div>
        )}
      </section>
      <p className="text-center text-xs text-sage-600">{t("eco.opportunities.disclaimer")}</p>
    </div>
  );
}

function FeaturedOpportunity({ o, personal }: { o: OpportunityCard; personal: boolean }) {
  const { t, i18n } = useTranslation();
  return (
    <section className="overflow-hidden rounded-3xl border border-cream-200/80 bg-white shadow-card md:grid md:grid-cols-[0.9fr_1.1fr]">
      <img src={coverFor(o.cover_key)} alt="" className="h-52 w-full object-cover md:h-full" />
      <div className="p-6 md:p-8">
        <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.25em] text-gold-600">
          <SparkIcon /> {personal ? t("eco.opportunities.forYou") : t("eco.opportunities.featured")}
        </p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          <Chip>{t(`eco.category.${o.category}`)}</Chip>
          <Chip tone="cream">{t(`eco.opportunities.type.${o.type}`)}</Chip>
          <MatchBadge match={o.match} />
        </div>
        <h2 className="mt-2 text-2xl leading-tight md:text-3xl">{o.title}</h2>
        <p className="mt-0.5 text-sm text-sage-600">{o.organization.name}</p>
        <p className="mt-2 leading-relaxed text-forest-700">{o.short_description}</p>
        <p className="mt-3 text-sm text-forest-700">
          {ageText(t, o.age_min, o.age_max)} · {locationText(t, o)} · {deadlineText(t, o.eligibility, o.application_deadline, i18n.language)}
        </p>
        {personal && (
          <ul className="mt-3 space-y-1.5">
            {o.match.reasons.slice(0, 3).map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-forest-700">
                <CheckIcon className="mt-0.5 h-4 w-4 shrink-0 text-forest-700" /> {reasonText(t, r)}
              </li>
            ))}
          </ul>
        )}
        <Link to={`/app/opportunities/${o.slug}`} className="btn-primary mt-5 gap-2">
          {t("eco.opportunities.viewDetails")} <ArrowIcon />
        </Link>
      </div>
    </section>
  );
}

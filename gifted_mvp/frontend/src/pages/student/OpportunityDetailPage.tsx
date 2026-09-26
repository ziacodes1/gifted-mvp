import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router-dom";
import { ecosystemApi } from "../../api/ecosystem";
import { Chip, DemoPill, LoadError, MatchBadge, PageSkeleton, WhyThisMatches } from "../../features/ecosystem/components";
import { heroCoverFor } from "../../features/ecosystem/covers";
import { BookmarkIcon, CalendarIcon, ExternalIcon, MonitorIcon, PeopleIcon, PinIcon } from "../../features/ecosystem/icons";
import { ageText, deadlineText, ECO_KEYS, locationText } from "../../features/ecosystem/lib";
import { BackIcon, CheckIcon, ChartIcon } from "../../features/passport/icons";
import type { OpportunityAction, OpportunityDetail } from "../../types/ecosystem";
import { formatDate } from "../../utils/date";

const TABS = ["overview", "details", "eligibility", "faqs"] as const;
type Tab = (typeof TABS)[number];

/** /app/opportunities/:slug — details, transparent fit, and a link to the provider's own application page. */
export function OpportunityDetailPage() {
  const { slug = "" } = useParams();
  const { t, i18n } = useTranslation();
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("overview");
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ECO_KEYS.opportunity(slug), queryFn: () => ecosystemApi.opportunity(slug) });
  const act = useMutation({
    mutationFn: (action: OpportunityAction) => ecosystemApi.opportunityAction(slug, action),
    onSuccess: (detail) => {
      qc.setQueryData(ECO_KEYS.opportunity(slug), detail);
      void qc.invalidateQueries({ queryKey: ["eco"], predicate: (q) => q.queryKey[1] !== "opportunity" });
    },
  });
  // Record a view once per visit (privacy-safe interaction state, no content).
  const viewed = useRef<string | null>(null);
  const { mutate } = act;
  useEffect(() => {
    if (data && viewed.current !== slug && data.state === "NONE") {
      viewed.current = slug;
      mutate("view");
    }
  }, [data, slug, mutate]);

  if (isLoading) return <PageSkeleton />;
  if (isError || !data) return <LoadError onRetry={() => void refetch()} />;
  const lang = i18n.language;
  const open = data.eligibility.open_now;
  const dates =
    data.program_start && data.program_end
      ? `${formatDate(data.program_start, lang)} – ${formatDate(data.program_end, lang)}`
      : data.program_start
        ? formatDate(data.program_start, lang)
        : null;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <header className="relative overflow-hidden rounded-3xl border border-cream-200/80 shadow-card">
        <div className="absolute inset-0 bg-cream-50" />
        <img src={heroCoverFor(data.cover_key)} alt="" className="absolute inset-y-0 right-0 h-full w-full object-cover object-right md:w-[55%]" />
        <div className="absolute inset-0 bg-gradient-to-r from-cream-50 via-cream-50/95 to-cream-50/10 md:from-45% md:via-cream-50/70 md:via-55% md:to-transparent" />
        <div className="relative max-w-2xl p-7 md:p-9">
          <Link to="/app/opportunities" className="inline-flex items-center gap-1.5 text-sm text-forest-700 hover:underline">
            <BackIcon /> {t("eco.opportunities.back")}
          </Link>
          <div className="mt-4 flex flex-wrap items-center gap-1.5">
            <Chip>{t(`eco.category.${data.category}`)}</Chip>
            <Chip tone="cream">{t(`eco.opportunities.type.${data.type}`)}</Chip>
            <DemoPill org={data.organization} />
          </div>
          <h1 className="mt-3 text-3xl leading-tight md:text-5xl">{data.title}</h1>
          <p className="mt-2 font-medium text-forest-800">{data.organization.name}</p>
          {data.organization.short_description && <p className="text-sm text-sage-600">{data.organization.short_description}</p>}
          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-forest-700">
            <span className="inline-flex items-center gap-1.5">
              <PinIcon /> {locationText(t, data)}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <PeopleIcon className="h-4 w-4" /> {ageText(t, data.age_min, data.age_max)}
            </span>
            {dates && (
              <span className="inline-flex items-center gap-1.5">
                <CalendarIcon /> {dates}
              </span>
            )}
            {data.mode !== "ONLINE" && (
              <span className="inline-flex items-center gap-1.5">
                <MonitorIcon /> {t(`eco.mode.${data.mode}`)}
              </span>
            )}
          </div>
          <p className={`mt-3 text-sm font-medium ${data.eligibility.deadline.status === "CLOSING_SOON" ? "text-gold-600" : "text-forest-700"}`}>
            {deadlineText(t, data.eligibility, data.application_deadline, lang)}
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            {open ? (
              <a href={data.application_url} target="_blank" rel="noopener noreferrer" onClick={() => act.mutate("open_link")} className="btn-primary gap-2 px-6 py-3">
                {t("eco.opportunities.apply")} <ExternalIcon />
              </a>
            ) : (
              <span className="inline-flex rounded-full bg-cream-200 px-6 py-3 text-sm font-medium text-sage-600">{t("eco.opportunities.notOpen")}</span>
            )}
            <button type="button" onClick={() => act.mutate(data.saved ? "unsave" : "save")} disabled={act.isPending} aria-pressed={data.saved} className="btn-ghost gap-2 bg-white/80 py-3">
              <BookmarkIcon className="h-4 w-4" filled={data.saved} /> {data.saved ? t("eco.opportunities.saved") : t("eco.opportunities.save")}
            </button>
          </div>
          <p className="mt-3 max-w-lg text-xs leading-relaxed text-sage-600">
            {data.state === "APPLICATION_LINK_OPENED"
              ? t("eco.opportunities.linkOpened", { org: data.organization.name })
              : t("eco.opportunities.applyNote", { org: data.organization.name })}
          </p>
          {data.organization.is_demo && <p className="mt-1 max-w-lg text-xs leading-relaxed text-sage-600">{t("eco.demo.listing")}</p>}
        </div>
      </header>

      <div className="grid items-start gap-6 lg:grid-cols-[1.5fr_1fr]">
        <div className="space-y-5">
          <div className="flex gap-1 overflow-x-auto border-b border-cream-200" role="tablist">
            {TABS.map((k) => (
              <button
                key={k}
                role="tab"
                aria-selected={tab === k}
                onClick={() => setTab(k)}
                className={`-mb-px whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition ${
                  tab === k ? "border-forest-700 text-forest-800" : "border-transparent text-sage-600 hover:text-forest-700"
                }`}
              >
                {t(`eco.opportunities.tabs.${k}`)}
              </button>
            ))}
          </div>
          <div role="tabpanel">{tabContent(tab, data, t, lang)}</div>
        </div>

        <aside className="space-y-4">
          <div className="card">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg">{t("eco.opportunities.yourFit")}</h2>
              <MatchBadge match={data.match} />
            </div>
            <p className="mt-1 text-xs text-sage-600">{t("eco.why.noScore")}</p>
          </div>
          {data.skills.length > 0 && (
            <div className="card">
              <h2 className="flex items-center gap-2 text-lg">
                <ChartIcon className="h-5 w-5 text-gold-600" /> {t("eco.opportunities.skills")}
              </h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {data.skills.map((s) => (
                  <span key={s} className="rounded-full bg-forest-50 px-3 py-1 text-xs text-forest-700">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}
          <div className="card">
            <h2 className="text-lg">{t("eco.opportunities.nextSteps.title")}</h2>
            <ol className="mt-3 space-y-2.5 text-sm text-forest-700">
              {[
                t("eco.opportunities.nextSteps.review"),
                t("eco.opportunities.nextSteps.open", { org: data.organization.name }),
                data.application_deadline
                  ? t("eco.opportunities.nextSteps.deadline", { date: formatDate(data.application_deadline, lang) })
                  : t("eco.opportunities.nextSteps.rolling"),
                t("eco.opportunities.nextSteps.updates", { org: data.organization.name }),
              ].map((s, i) => (
                <li key={i} className="flex items-start gap-2.5">
                  <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-gold-400 text-[11px] font-semibold text-forest-900">{i + 1}</span>
                  {s}
                </li>
              ))}
            </ol>
          </div>
        </aside>
      </div>
    </div>
  );
}

function tabContent(tab: Tab, data: OpportunityDetail, t: ReturnType<typeof useTranslation>["t"], lang: string) {
  if (tab === "overview") {
    return (
      <div className="space-y-5">
        <WhyThisMatches match={data.match} />
        <div className="card">
          <h2 className="text-xl">{t("eco.opportunities.overview")}</h2>
          <p className="mt-2 leading-relaxed text-forest-700">{data.description || data.short_description}</p>
        </div>
      </div>
    );
  }
  if (tab === "details") {
    const rows: [string, string | null][] = [
      [t("eco.opportunities.detail.type"), t(`eco.opportunities.type.${data.type}`)],
      [t("eco.opportunities.detail.provider"), data.organization.name],
      [t("eco.opportunities.detail.format"), locationText(t, data)],
      [t("eco.opportunities.detail.opens"), data.application_open_at ? formatDate(data.application_open_at, lang) : null],
      [t("eco.opportunities.detail.deadline"), data.application_deadline ? formatDate(data.application_deadline, lang) : t("eco.opportunities.deadline.rolling")],
      [t("eco.opportunities.detail.starts"), data.program_start ? formatDate(data.program_start, lang) : null],
      [t("eco.opportunities.detail.ends"), data.program_end ? formatDate(data.program_end, lang) : null],
    ];
    return (
      <dl className="card divide-y divide-cream-200">
        {rows
          .filter(([, v]) => v)
          .map(([k, v]) => (
            <div key={k} className="grid grid-cols-[10rem_1fr] gap-3 py-2.5 text-sm">
              <dt className="text-sage-600">{k}</dt>
              <dd className="text-forest-800">{v}</dd>
            </div>
          ))}
      </dl>
    );
  }
  if (tab === "eligibility") {
    const e = data.eligibility;
    return (
      <div className="card space-y-4">
        <ul className="space-y-2.5 text-sm text-forest-700">
          <li className="flex items-start gap-2">
            <PeopleIcon className="mt-0.5 h-4 w-4 shrink-0" />
            {e.age.status === "CHECK" ? t("eco.opportunities.elig.age", { range: ageText(t, e.age.min, e.age.max) }) : t("eco.opportunities.elig.anyAge")}
          </li>
          <li className="flex items-start gap-2">
            <PinIcon className="mt-0.5 h-4 w-4 shrink-0" />
            {t(`eco.opportunities.elig.location.${e.location.status}`, { place: [e.location.city, e.location.country].filter(Boolean).join(", "), country: e.location.country })}
          </li>
        </ul>
        {data.requirements.length > 0 && (
          <div>
            <h3 className="text-base">{t("eco.opportunities.elig.requirements")}</h3>
            <ul className="mt-2 space-y-1.5">
              {data.requirements.map((r) => (
                <li key={r} className="flex items-start gap-2 text-sm text-forest-700">
                  <CheckIcon className="mt-0.5 h-4 w-4 shrink-0" /> {r}
                </li>
              ))}
            </ul>
          </div>
        )}
        <p className="text-xs text-sage-600">{t("eco.opportunities.elig.note", { org: data.organization.name })}</p>
      </div>
    );
  }
  return (
    <div className="space-y-3">
      {data.faqs.length === 0 && <p className="card text-sm text-sage-600">{t("eco.opportunities.noFaqs")}</p>}
      {data.faqs.map((f) => (
        <details key={f.q} className="card group">
          <summary className="cursor-pointer list-none font-medium text-forest-800">{f.q}</summary>
          <p className="mt-2 text-sm leading-relaxed text-forest-700">{f.a}</p>
        </details>
      ))}
    </div>
  );
}

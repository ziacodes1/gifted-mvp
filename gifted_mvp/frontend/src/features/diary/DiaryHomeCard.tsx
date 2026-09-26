import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { diaryApi } from "../../api/diary";
import { ArrowIcon, BookIcon } from "../passport/icons";
import { DaisySprig, MoodFace } from "./decor";
import { PenIcon } from "./DiaryHomeSections";
import { DIARY_OVERVIEW_KEY } from "./queries";
import { formatEntryDate } from "./format";

/** Student Home: latest page (or empty state), page progress and a way in. */
export function DiaryHomeCard() {
  const { t, i18n } = useTranslation();
  const { data } = useQuery({ queryKey: DIARY_OVERVIEW_KEY, queryFn: diaryApi.overview });
  if (!data) return <div className="h-40 animate-pulse rounded-2xl bg-white shadow-card" />;
  const latest = data.recent_entries[0];
  const pct = Math.min(data.pages_filled / data.page_target, 1) * 100;

  return (
    <section className="card relative overflow-hidden bg-gradient-to-br from-white to-[#fbf6ea]">
      <DaisySprig className="pointer-events-none absolute -right-2 -top-4 h-36 w-12 opacity-80" />
      <div className="flex flex-col gap-5 pr-8 sm:flex-row sm:items-center">
        <div className="flex items-center gap-4 sm:w-64">
          <span className="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-gold-50 text-gold-600">
            <BookIcon className="h-6 w-6" />
          </span>
          <div className="min-w-0 flex-1">
            <h2 className="text-xl">{t("diary.home.title")}</h2>
            <p className="text-xs text-sage-600">{t("diary.pagesFilled", { count: data.pages_filled, total: data.page_target })}</p>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-cream-200">
              <div className="h-full rounded-full bg-forest-700" style={{ width: `${pct}%` }} />
            </div>
          </div>
        </div>

        <div className="min-w-0 flex-1 rounded-2xl border border-dashed border-[#e2d5b8] bg-[#fbf6ea] px-4 py-3">
          {latest ? (
            <Link to={`/app/diary/${latest.id}`} className="flex items-center gap-3">
              <span className="min-w-0 flex-1">
                <span className="block text-[11px] uppercase tracking-wider text-sage-600">
                  {t("diary.home.latest")} · {formatEntryDate(latest.entry_date, i18n.resolvedLanguage)}
                </span>
                <span className="block truncate font-hand text-2xl leading-tight text-forest-800">{latest.title || t("diary.untitled")}</span>
              </span>
              {latest.mood && <MoodFace mood={latest.mood} className="h-8 w-8 shrink-0" />}
            </Link>
          ) : (
            <p className="font-hand text-2xl leading-tight text-forest-800">{t("diary.home.empty")}</p>
          )}
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          <Link to="/app/diary/new" className="btn-primary gap-2">
            <PenIcon className="h-4 w-4" /> {t("diary.home.write")}
          </Link>
          {latest && (
            <Link to="/app/diary" className="btn-ghost gap-2">
              {t("diary.home.open")} <ArrowIcon />
            </Link>
          )}
        </div>
      </div>
    </section>
  );
}

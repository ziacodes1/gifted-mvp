import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { diaryApi } from "../../api/diary";
import {
  CompanionSuggestion,
  DiaryBookPreview,
  DiaryHero,
  DiaryPrivacyCard,
  MoodSummary,
  PenIcon,
  RecentEntries,
} from "../../features/diary/DiaryHomeSections";
import { DIARY_OVERVIEW_KEY } from "../../features/diary/queries";
import { ArrowIcon, BookIcon } from "../../features/passport/icons";

/** /app/diary — the learner's private journal. */
export function DiaryPage() {
  const { t } = useTranslation();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: DIARY_OVERVIEW_KEY, queryFn: diaryApi.overview });
  const latest = data?.recent_entries[0];

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <DiaryHero />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div>
          {isLoading ? (
            <div className="h-[30rem] animate-pulse rounded-[26px] bg-forest-50" />
          ) : isError || !data ? (
            <div className="card text-center">
              <p className="text-sm text-sage-600">{t("diary.editor.loadError")}</p>
              <button onClick={() => void refetch()} className="btn-ghost mt-3">
                {t("common.retry")}
              </button>
            </div>
          ) : (
            <>
              <DiaryBookPreview overview={data} />
              {latest && (
                <div className="-mt-4 flex flex-wrap justify-center gap-3">
                  <Link to={`/app/diary/${latest.id}`} className="btn-primary gap-2 px-6 py-3">
                    <BookIcon className="h-4 w-4" /> {t("diary.open")} <ArrowIcon />
                  </Link>
                  <Link to="/app/diary/new" className="btn-ghost gap-2 bg-white px-6 py-3">
                    <PenIcon className="h-4 w-4" /> {t("diary.newEntry")}
                  </Link>
                </div>
              )}
            </>
          )}
        </div>

        <aside className="space-y-5">
          <RecentEntries entries={data?.recent_entries ?? []} />
          <MoodSummary week={data?.mood_week ?? []} />
          <DiaryPrivacyCard />
          {data && <CompanionSuggestion pending={data.pending_moment} />}
        </aside>
      </div>
    </div>
  );
}

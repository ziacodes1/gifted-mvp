import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { companionApi } from "../../api/companion";
import { diaryApi } from "../../api/diary";
import heroImage from "../../assets/diary/diary_hero.webp";
import type { DiaryEntrySummary, DiaryOverview } from "../../types/diary";
import { ArrowIcon, BookIcon, ChartIcon, ChevronIcon, LeafIcon, LockIcon, SparkIcon } from "../passport/icons";
import { DaisySprig, FernSketch, LeafBranch, MoodFace, Sticker, Tape } from "./decor";
import { DiaryBook, Polaroid } from "./DiaryBook";
import { DIARY_OVERVIEW_KEY, usePhotoUrl } from "./queries";
import { formatWeekday } from "../../utils/date";
import { formatEntryDate, parseDay } from "./format";

/* ------------------------------------------------------------------ hero */

export function DiaryHero() {
  const { t } = useTranslation();
  const features = [
    { key: "reflect", icon: <LeafIcon className="h-6 w-6" /> },
    { key: "photos", icon: <CameraIcon /> },
    { key: "write", icon: <PenIcon /> },
    { key: "growth", icon: <ChartIcon className="h-6 w-6" /> },
  ];
  return (
    <div className="relative overflow-hidden rounded-3xl border border-cream-200/80 shadow-card">
      <img src={heroImage} alt="" className="absolute inset-0 h-full w-full object-cover object-[75%_35%]" />
      <div className="absolute inset-0 bg-gradient-to-r from-cream-50 via-cream-50/90 to-cream-50/0 md:via-cream-50/70" />
      <div className="relative max-w-2xl p-7 md:px-10 md:py-9">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-forest-600">{t("diary.eyebrow")}</p>
        <h1 className="mt-3 text-4xl leading-[1.08] md:text-5xl">
          {t("diary.titleA")} <span className="block text-gold-600">{t("diary.titleB")}</span>
        </h1>
        <p className="mt-4 max-w-lg leading-relaxed text-forest-700/85">{t("diary.intro")}</p>
        <ul className="mt-6 grid grid-cols-2 gap-x-6 gap-y-3 text-sm sm:flex sm:flex-wrap">
          {features.map((f) => (
            <li key={f.key} className="flex items-center gap-2.5">
              <span className="text-forest-700">{f.icon}</span>
              <span className="leading-tight">
                <span className="block font-medium text-forest-700">{t(`diary.features.${f.key}.a`)}</span>
                <span className="text-sage-600">{t(`diary.features.${f.key}.b`)}</span>
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ book */

export function DiaryProgress({ filled, target }: { filled: number; target: number }) {
  const { t } = useTranslation();
  const left = Math.max(target - filled, 0);
  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
      <div className="flex items-center gap-3">
        <span className="grid h-11 w-11 place-items-center rounded-full bg-gold-50 text-gold-600">
          <BookIcon className="h-6 w-6" />
        </span>
        <div>
          <h2 className="text-2xl leading-tight">{t("diary.bookTitle")}</h2>
          <p className="text-sm text-forest-700">{t("diary.pagesFilled", { count: filled, total: target })}</p>
        </div>
      </div>
      <div
        className="h-2.5 min-w-[8rem] flex-1 overflow-hidden rounded-full bg-cream-200"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={target}
        aria-valuenow={Math.min(filled, target)}
        aria-label={t("diary.pagesFilled", { count: filled, total: target })}
      >
        <div className="h-full rounded-full bg-forest-700 transition-all" style={{ width: `${Math.min(filled / target, 1) * 100}%` }} />
      </div>
      <p className="font-hand text-xl leading-tight text-forest-700" title={t("diary.pageRule")}>
        {left > 0 ? t("diary.pagesMore", { count: left }) : t("diary.pagesComplete")}
      </p>
    </div>
  );
}

export function DiaryBookPreview({ overview }: { overview: DiaryOverview }) {
  const { t } = useTranslation();
  const [first, ...rest] = overview.book_pages;
  const header = <DiaryProgress filled={overview.pages_filled} target={overview.page_target} />;

  if (!first) {
    return (
      <DiaryBook
        header={header}
        left={
          <div className="relative flex h-full flex-col justify-center py-4 pl-8 md:pl-10">
            <DaisySprig className="absolute -left-3 top-0 h-52 w-16 md:-left-6" />
            <p className="font-hand text-4xl leading-tight text-forest-800">{t("diary.emptyTitle")}</p>
            <p className="mt-3 max-w-sm leading-relaxed text-forest-700/85">{t("diary.emptyText")}</p>
            <Link to="/app/diary/new" className="btn-primary mt-6 gap-2 self-start px-6 py-3">
              <PenIcon className="h-4 w-4" /> {t("diary.firstEntry")}
            </Link>
          </div>
        }
        right={
          <div className="relative h-full">
            <div className="diary-lines h-56 pr-2 font-hand text-2xl text-sage-600/80">{t("diary.emptyPage")}</div>
            <LeafBranch className="absolute bottom-0 right-2 h-20 w-20 opacity-90" />
            <Sticker id="sprout" className="absolute bottom-2 left-2 h-12 w-12" />
          </div>
        }
      />
    );
  }

  return (
    <DiaryBook
      header={header}
      left={
        <div className="relative pl-7 md:pl-9">
          <DaisySprig className="absolute -left-4 top-2 h-56 w-16 md:-left-7" />
          <BookPageEntry entry={first} large />
        </div>
      }
      right={
        <div className="relative space-y-5">
          {rest.length === 0 ? (
            <div className="grid h-full min-h-[14rem] place-items-center">
              <Link to="/app/diary/new" className="group text-center">
                <p className="font-hand text-3xl text-forest-700 group-hover:text-forest-800">{t("diary.newEntry")} ✎</p>
                <p className="mt-1 font-hand text-xl text-sage-600">{t("diary.pageRule")}</p>
              </Link>
            </div>
          ) : (
            rest.map((e, i) => (
              <div key={e.id} className={i > 0 ? "border-t border-dashed border-[#e2d5b8] pt-5" : ""}>
                <BookPageEntry entry={e} />
              </div>
            ))
          )}
          <FernSketch className="absolute -bottom-6 right-0 h-16 w-12 opacity-80" />
        </div>
      }
    />
  );
}

function BookPageEntry({ entry, large = false }: { entry: DiaryEntrySummary; large?: boolean }) {
  const { t, i18n } = useTranslation();
  return (
    <Link to={`/app/diary/${entry.id}`} className="group flow-root rounded-xl outline-none focus-visible:ring-2 focus-visible:ring-forest-600/30">
      {/* A taped print the handwriting flows around. */}
      {entry.cover_photo &&
        (large ? (
          <Polaroid photoId={entry.cover_photo.id} tilt={3} className="float-right mb-3 ml-4 mt-2 w-36 md:w-44" />
        ) : (
          <Polaroid photoId={entry.cover_photo.id} tilt={-3} tape="sage" className="float-left mb-2 mr-4 mt-1 w-28" />
        ))}
      <div>
        <div className="min-w-0">
          <p className="text-[13px] font-medium tracking-wide text-[#35507a]">{formatEntryDate(entry.entry_date, i18n.resolvedLanguage)}</p>
          <p className={`mt-1 font-hand font-semibold leading-tight text-forest-800 group-hover:text-forest-900 ${large ? "text-3xl" : "text-2xl"}`}>
            {entry.title || t("diary.untitled")}
          </p>
          {entry.excerpt && (
            <p className={`mt-1.5 whitespace-pre-line font-hand leading-snug text-[#2b3f5c] ${large ? "line-clamp-[9] text-[1.35rem]" : "line-clamp-4 text-xl"}`}>
              {entry.excerpt}
            </p>
          )}
        </div>
      </div>
      <div className="clear-both flex flex-wrap items-center gap-2 pt-3">
        {entry.mood && (
          <span className="relative inline-flex items-center gap-2 px-3 py-1 font-hand text-xl text-forest-800">
            <Tape tone="sage" className="absolute inset-0 -z-0 h-full w-full" />
            <span className="relative">{t(`diary.mood.${entry.mood}`)}</span>
            <MoodFace mood={entry.mood} className="relative h-6 w-6" />
          </span>
        )}
        {entry.source === "COMPANION" && (
          <span className="inline-flex items-center gap-1 rounded-full bg-forest-50 px-2 py-0.5 text-[11px] text-forest-700">
            <SparkIcon className="h-3 w-3" /> {t("diary.fromCompanion")}
          </span>
        )}
        {entry.stickers.slice(0, 3).map((s) => (
          <Sticker key={s.slot} id={s.id} className="h-8 w-8" />
        ))}
      </div>
    </Link>
  );
}

/* ------------------------------------------------------------------ side cards */

function SideCard({ title, icon, action, children }: { title: string; icon: ReactNode; action?: ReactNode; children: ReactNode }) {
  return (
    <section className="rounded-3xl border border-cream-200/60 bg-white p-5 shadow-card">
      <div className="flex items-center justify-between gap-3">
        <h2 className="flex items-center gap-2.5 text-xl">
          <span className="text-gold-600">{icon}</span> {title}
        </h2>
        {action}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function EntryRow({ entry }: { entry: DiaryEntrySummary }) {
  const { t, i18n } = useTranslation();
  const thumb = usePhotoUrl(entry.cover_photo?.id);
  return (
    <Link to={`/app/diary/${entry.id}`} className="flex items-center gap-3 rounded-2xl px-2 py-2 transition hover:bg-cream-50">
      <span className="grid h-12 w-14 shrink-0 place-items-center overflow-hidden rounded-xl bg-cream-100">
        {entry.cover_photo ? (
          thumb ? <img src={thumb} alt="" className="h-full w-full object-cover" /> : <span className="h-full w-full animate-pulse bg-cream-200" />
        ) : (
          <BookIcon className="h-5 w-5 text-sage-600" />
        )}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-forest-700">{entry.title || t("diary.untitled")}</span>
        <span className="text-xs text-sage-600">{formatEntryDate(entry.entry_date, i18n.resolvedLanguage)}</span>
      </span>
      {entry.mood && <MoodFace mood={entry.mood} className="h-7 w-7 shrink-0" />}
      <ChevronIcon className="h-4 w-4 shrink-0 text-sage-600" />
    </Link>
  );
}

export function RecentEntries({ entries }: { entries: DiaryEntrySummary[] }) {
  const { t } = useTranslation();
  const [all, setAll] = useState(false);
  return (
    <SideCard
      title={t("diary.recent.title")}
      icon={<BookIcon />}
      action={
        entries.length >= 5 && (
          <button onClick={() => setAll((v) => !v)} className="inline-flex items-center gap-1 text-sm font-medium text-forest-700 hover:underline">
            {all ? t("diary.recent.showLess") : t("diary.recent.seeAll")} {!all && <ArrowIcon />}
          </button>
        )
      }
    >
      {entries.length === 0 ? (
        <p className="text-sm text-sage-600">{t("diary.recent.empty")}</p>
      ) : all ? (
        <AllEntries />
      ) : (
        <div className="-mx-2 space-y-0.5">
          {entries.map((e) => (
            <EntryRow key={e.id} entry={e} />
          ))}
        </div>
      )}
    </SideCard>
  );
}

function AllEntries() {
  const { t } = useTranslation();
  const q = useInfiniteQuery({
    queryKey: ["diary-entries", "all"],
    queryFn: ({ pageParam }) => diaryApi.list({ page: pageParam, page_size: 20 }),
    initialPageParam: 1,
    getNextPageParam: (last, pages) => (last.next ? pages.length + 1 : undefined),
  });
  const entries = q.data?.pages.flatMap((p) => p.results) ?? [];
  return (
    <div className="-mx-2 max-h-[28rem] space-y-0.5 overflow-y-auto">
      {entries.map((e) => (
        <EntryRow key={e.id} entry={e} />
      ))}
      {q.hasNextPage && (
        <button onClick={() => void q.fetchNextPage()} disabled={q.isFetchingNextPage} className="btn-ghost mx-2 mt-2 w-[calc(100%-1rem)] py-2">
          {t("diary.recent.loadMore")}
        </button>
      )}
    </div>
  );
}

export function MoodSummary({ week }: { week: DiaryOverview["mood_week"] }) {
  const { t, i18n } = useTranslation();
  const any = week.some((d) => d.mood);
  return (
    <SideCard title={t("diary.moodWeek.title")} icon={<ChartIcon />}>
      <ol className="grid grid-cols-7 gap-1 text-center">
        {week.map((d) => (
          <li key={d.date} className="flex flex-col items-center gap-1.5">
            {d.mood ? (
              <span title={t(`diary.mood.${d.mood}`)}>
                <MoodFace mood={d.mood} className="h-8 w-8" />
                <span className="sr-only">{t(`diary.mood.${d.mood}`)}</span>
              </span>
            ) : (
              <span className="grid h-8 w-8 place-items-center rounded-full border border-dashed border-sage-200" aria-hidden />
            )}
            <span className="text-[11px] text-sage-600">
              {formatWeekday(parseDay(d.date), i18n.resolvedLanguage)}
            </span>
          </li>
        ))}
      </ol>
      {!any && <p className="mt-3 text-xs text-sage-600">{t("diary.moodWeek.empty")}</p>}
    </SideCard>
  );
}

export function DiaryPrivacyCard() {
  const { t } = useTranslation();
  return (
    <section className="relative overflow-hidden rounded-3xl border border-forest-700/10 bg-forest-50/70 px-5 py-4">
      <div className="flex items-start gap-3">
        <LockIcon className="mt-0.5 h-5 w-5 shrink-0 text-forest-700" />
        <div className="pr-10">
          <p className="font-medium text-forest-700">{t("diary.privacy.title")}</p>
          <p className="mt-0.5 text-xs leading-relaxed text-forest-700/80">{t("diary.privacy.text")}</p>
        </div>
      </div>
      <LeafBranch className="absolute -bottom-3 -right-2 h-16 w-16 opacity-70" />
    </section>
  );
}

/** A real pending offer from the Companion (student's own words), or a quiet link to the Companion. */
export function CompanionSuggestion({ pending }: { pending: DiaryOverview["pending_moment"] }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const dismiss = useMutation({
    mutationFn: () => companionApi.dismissDiaryOffer(pending!.assistant_message_id),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: DIARY_OVERVIEW_KEY });
      void qc.invalidateQueries({ queryKey: ["companion-conversation"] });
    },
  });
  return (
    <section className="rounded-3xl border border-gold-400/40 bg-gradient-to-br from-gold-50 to-white p-5 shadow-soft">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-forest-50 text-forest-700">
          <SparkIcon className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-serif text-lg text-forest-700">{pending ? t("diary.companion.title") : t("diary.companion.idleTitle")}</p>
          {pending ? (
            <>
              <p className="mt-1 text-sm text-sage-600">{t("diary.companion.pending")}</p>
              <blockquote className="mt-2 border-l-2 border-gold-400 pl-3 font-hand text-xl leading-snug text-forest-800">“{pending.excerpt}”</blockquote>
              <div className="mt-3 flex flex-wrap gap-2">
                <button onClick={() => navigate(`/app/diary/new?from=${pending.student_message_id}`)} className="btn-primary px-4 py-2 text-xs">
                  {t("diary.companion.add")}
                </button>
                <button onClick={() => dismiss.mutate()} disabled={dismiss.isPending} className="btn-ghost px-4 py-2 text-xs">
                  {t("diary.companion.dismiss")}
                </button>
              </div>
            </>
          ) : (
            <>
              <p className="mt-1 text-sm leading-relaxed text-sage-600">{t("diary.companion.idleText")}</p>
              <Link to="/app/companion" className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-forest-700 hover:underline">
                {t("diary.companion.open")} <ArrowIcon />
              </Link>
            </>
          )}
        </div>
      </div>
    </section>
  );
}

/* ------------------------------------------------------------------ small icons */

export function PenIcon({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d="m15.5 4.5 4 4L9 19l-5 1 1-5Z" />
      <path d="m13.5 6.5 4 4" />
    </svg>
  );
}

export function CameraIcon({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden>
      <path d="M4 8h3l1.5-2.5h7L17 8h3v11H4Z" />
      <circle cx="12" cy="13" r="3.5" />
    </svg>
  );
}

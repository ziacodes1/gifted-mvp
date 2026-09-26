import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { companionApi } from "../../api/companion";
import { diaryApi } from "../../api/diary";
import type { CompanionMessage, Conversation } from "../../types/companion";
import { formatEntryDate } from "../diary/format";
import { ArrowIcon, BookIcon, CheckIcon, ChevronIcon } from "../passport/icons";
import { conversationKey } from "./useCompanionChat";

/** Under an assistant reply the model flagged as a meaningful moment. Nothing is saved here:
 * "Add to My Diary" opens the editor prefilled with the student's own words. */
export function DiaryOfferCard({ message, conversationId }: { message: CompanionMessage; conversationId: number }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [busy, setBusy] = useState(false);
  const diary = message.diary;
  if (!diary || !diary.student_message_id) return null;

  if (diary.entry_id) {
    return (
      <Link to={`/app/diary/${diary.entry_id}`} className="inline-flex items-center gap-1.5 text-xs font-medium text-forest-700 hover:underline">
        <CheckIcon className="h-3.5 w-3.5" /> {t("companion.offer.saved")} · {t("companion.offer.open")}
      </Link>
    );
  }
  if (diary.offer !== "OFFERED") return null;

  const keepInChat = async () => {
    setBusy(true);
    try {
      await companionApi.dismissDiaryOffer(message.id);
      qc.setQueryData<Conversation>(conversationKey(conversationId), (old) =>
        old && {
          ...old,
          messages: old.messages.map((m) => (m.id === message.id && m.diary ? { ...m, diary: { ...m.diary, offer: "DISMISSED" } } : m)),
        },
      );
      void qc.invalidateQueries({ queryKey: ["diary-overview"] });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-gold-400/50 bg-gold-50/70 p-4 sm:flex-row sm:items-center">
      <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-white text-gold-600 shadow-soft">
        <BookIcon className="h-5 w-5" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-serif text-[15px] leading-snug text-forest-800">{t("companion.offer.text")}</p>
        <p className="mt-0.5 text-xs text-sage-600">{t("companion.offer.sub")}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => navigate(`/app/diary/new?from=${diary.student_message_id}`)}
            className="btn-primary gap-2 px-4 py-2 text-xs"
          >
            <BookIcon className="h-4 w-4" /> {t("companion.offer.add")} <ArrowIcon className="h-3.5 w-3.5" />
          </button>
          <button type="button" onClick={() => void keepInChat()} disabled={busy} className="btn-ghost bg-white px-4 py-2 text-xs">
            {t("companion.offer.keep")}
          </button>
        </div>
      </div>
    </div>
  );
}

/** Right column on the Companion page: only entries saved from Companion chats. */
export function DiaryMoments() {
  const { t, i18n } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["diary-entries", "COMPANION"],
    queryFn: () => diaryApi.list({ source: "COMPANION", page_size: 3 }),
  });
  const entries = data?.results ?? [];
  return (
    <section className="rounded-3xl border border-cream-200/60 bg-white p-5 shadow-card">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-forest-50 text-forest-700">
          <BookIcon />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <h2 className="text-xl leading-tight">{t("companion.diary.title")}</h2>
            <Link to="/app/diary" className="inline-flex shrink-0 items-center gap-1 text-xs font-medium text-forest-700 hover:underline">
              {t("companion.diary.seeAll")} <ArrowIcon className="h-3.5 w-3.5" />
            </Link>
          </div>
          <p className="mt-0.5 text-sm leading-snug text-sage-600">{t("companion.diary.subtitle")}</p>
        </div>
      </div>
      <div className="mt-4">
        {isLoading ? (
          <div className="h-14 animate-pulse rounded-2xl bg-cream-100" />
        ) : entries.length === 0 ? (
          <p className="rounded-2xl bg-cream-50 p-3 text-sm leading-relaxed text-sage-600">{t("companion.diary.empty")}</p>
        ) : (
          <ul className="-mx-2">
            {entries.map((e) => (
              <li key={e.id}>
                <Link to={`/app/diary/${e.id}`} className="flex items-center gap-3 rounded-2xl px-2 py-2 hover:bg-cream-50">
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-forest-700">{e.title || t("diary.untitled")}</span>
                    <span className="block truncate font-hand text-lg leading-tight text-[#2b3f5c]">{e.excerpt}</span>
                    <span className="text-[11px] text-sage-600">{formatEntryDate(e.entry_date, i18n.resolvedLanguage)}</span>
                  </span>
                  <ChevronIcon className="h-4 w-4 shrink-0 text-sage-600" />
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

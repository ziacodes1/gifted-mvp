import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation } from "react-router-dom";
import { todayApi } from "../../api/today";
import type { Nudge, Today } from "../../types/today";
import { formatDate } from "../../utils/date";
import { TODAY_KEY } from "./sparkText";

/** In-app updates only (no push/email). Built from real state by the backend. */
export function NudgeBell() {
  const { t, i18n } = useTranslation();
  const qc = useQueryClient();
  const { data, refetch, dataUpdatedAt } = useQuery({ queryKey: TODAY_KEY, queryFn: todayApi.get, staleTime: 60_000 });
  // The bell lives in the layout (it never remounts), so refresh it on navigation when stale.
  const { pathname } = useLocation();
  useEffect(() => {
    if (dataUpdatedAt && Date.now() - dataUpdatedAt > 30_000) void refetch();
  }, [pathname]); // eslint-disable-line react-hooks/exhaustive-deps
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => !ref.current?.contains(e.target as Node) && setOpen(false);
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next && data?.unread) {
      void todayApi.markSeen();
      qc.setQueryData<Today>(TODAY_KEY, (old) => old && { ...old, unread: 0 });
    }
  };

  const text = (n: Nudge) =>
    n.kind === "badge"
      ? t("nudges.kinds.badge", { badge: t(`rewards.badges.items.${n.params.badge}.title`) })
      : t(`nudges.kinds.${n.kind}`, n.params);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={toggle}
        aria-expanded={open}
        aria-label={t("nudges.open")}
        className="relative grid h-10 w-10 place-items-center rounded-full border border-cream-200 bg-white text-forest-700 shadow-soft transition hover:bg-cream-50"
      >
        <BellIcon />
        {!!data?.unread && (
          <span data-testid="nudge-count" className="absolute -right-0.5 -top-0.5 grid h-4 min-w-4 place-items-center rounded-full bg-gold-500 px-1 text-[10px] font-semibold text-forest-900">
            {data.unread}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-30 mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-2xl border border-cream-200 bg-white p-2 shadow-card">
          <p className="px-3 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wider text-sage-600">{t("nudges.title")}</p>
          {!data?.nudges.length ? (
            <p className="px-3 py-3 text-sm text-sage-600">{t("nudges.empty")}</p>
          ) : (
            <ul className="max-h-80 overflow-y-auto">
              {data.nudges.map((n, i) => (
                <li key={i}>
                  <Link to={n.to} onClick={() => setOpen(false)} className="flex items-start gap-3 rounded-xl px-3 py-2.5 hover:bg-cream-50">
                    <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${n.unread ? "bg-gold-500" : "bg-cream-200"}`} />
                    <span className="min-w-0">
                      <span className="block text-sm text-forest-700">{text(n)}</span>
                      <span className="text-[11px] text-sage-600">{formatDate(n.at, i18n.resolvedLanguage)}</span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

function BellIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5" aria-hidden>
      <path d="M6 16.5V11a6 6 0 1 1 12 0v5.5l1.5 2h-15Z" />
      <path d="M10 20.5a2 2 0 0 0 4 0" />
    </svg>
  );
}

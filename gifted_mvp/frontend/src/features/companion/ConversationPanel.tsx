import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { useAuth } from "../auth/AuthContext";
import { ChevronIcon, HistoryIcon, PlusIcon, SendIcon, SparkIcon } from "../passport/icons";
import { formatDate } from "../../utils/date";
import type { CompanionMessage, ConversationSummary } from "../../types/companion";
import type { PendingTurn } from "./useCompanionChat";

const MAX_CHARS = 2000;

interface Props {
  firstName: string;
  messages: CompanionMessage[];
  conversations: ConversationSummary[];
  activeId: number | null;
  loading: boolean;
  loadError: boolean;
  pending: PendingTurn | null;
  sending: boolean;
  creating: boolean;
  onSend: (text: string) => Promise<boolean>;
  onRetry: () => void;
  onNewChat: () => void;
  onOpen: (id: number) => void;
  /** Extension point for per-message actions (e.g. a later "Add to My Diary"). */
  renderAssistantActions?: (message: CompanionMessage) => ReactNode;
}

export function ConversationPanel(props: Props) {
  const { t } = useTranslation();
  const { messages, pending, loading, loadError, sending } = props;
  const scrollRef = useRef<HTMLDivElement>(null);

  // Keep the newest message in view.
  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length, pending?.status, props.activeId]);

  return (
    <section className="flex min-h-[560px] flex-col overflow-hidden rounded-3xl border border-cream-200/60 bg-white shadow-card lg:h-[640px]">
      <header className="flex items-center justify-between gap-3 border-b border-cream-200/70 px-5 py-4 md:px-7">
        <div className="flex min-w-0 items-center gap-3.5">
          <span className="hidden sm:block">
            <CompanionAvatar size="lg" />
          </span>
          <div className="min-w-0">
            <h2 className="truncate text-xl leading-tight sm:text-2xl">{t("companion.panelTitle")}</h2>
            <p className="truncate text-sm text-sage-600">{t("companion.panelSubtitle")}</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button onClick={props.onNewChat} disabled={sending || props.creating} className="btn-ghost gap-2 px-4 py-2">
            <PlusIcon /> <span className="hidden sm:inline">{t("companion.newChat")}</span>
          </button>
          <RecentChats conversations={props.conversations} activeId={props.activeId} onOpen={props.onOpen} disabled={sending} />
        </div>
      </header>

      <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto px-4 py-6 md:px-7" aria-live="polite">
        {loading ? (
          <div className="space-y-4" aria-hidden>
            <div className="h-20 w-3/4 animate-pulse rounded-2xl bg-cream-100" />
            <div className="ml-auto h-14 w-1/2 animate-pulse rounded-2xl bg-forest-50" />
          </div>
        ) : loadError ? (
          <p className="text-center text-sm text-sage-600">{t("companion.loadError")}</p>
        ) : (
          <>
            {messages.length === 0 && !pending && (
              <MessageBubble role="ASSISTANT" content={t("companion.welcome", { name: props.firstName })} />
            )}
            {messages.map((m) => (
              <MessageBubble
                key={m.id}
                role={m.role}
                content={m.content}
                time={m.created_at}
                actions={m.role === "ASSISTANT" ? props.renderAssistantActions?.(m) : undefined}
              />
            ))}
            {pending && <MessageBubble role="USER" content={pending.content} dimmed={pending.status === "sending"} />}
            {pending?.status === "sending" && <ThinkingBubble />}
            {pending?.status === "failed" && (
              <div role="alert" className="ml-12 flex flex-wrap items-center gap-3 rounded-2xl border border-gold-400/40 bg-gold-50 px-4 py-3 text-sm text-forest-700">
                <span>{t("companion.error")}</span>
                <button onClick={props.onRetry} className="font-medium text-forest-700 underline underline-offset-2 hover:text-forest-800">
                  {t("companion.retry")}
                </button>
              </div>
            )}
          </>
        )}
      </div>

      <ConversationComposer
        onSend={props.onSend}
        disabled={sending || props.creating}
      />
    </section>
  );
}

export function CompanionAvatar({ size = "sm" }: { size?: "sm" | "lg" }) {
  const box = size === "lg" ? "h-12 w-12" : "h-9 w-9";
  return (
    <span className={`grid ${box} shrink-0 place-items-center rounded-full bg-forest-50 text-forest-700`}>
      <SparkIcon className={size === "lg" ? "h-6 w-6" : "h-4 w-4"} />
    </span>
  );
}

function UserAvatar() {
  const { user } = useAuth();
  const name = user?.full_name?.trim() || user?.email || "";
  const initials = name.split(/[\s@.]+/).filter(Boolean).slice(0, 2).map((p) => p[0]!.toUpperCase()).join("");
  return (
    <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gold-50 text-xs font-semibold text-gold-600">
      {initials || "•"}
    </span>
  );
}

export function MessageBubble({
  role,
  content,
  time,
  dimmed,
  actions,
}: {
  role: "USER" | "ASSISTANT";
  content: string;
  time?: string;
  dimmed?: boolean;
  actions?: ReactNode;
}) {
  const { t, i18n } = useTranslation();
  const mine = role === "USER";
  return (
    <div className={`flex items-end gap-3 animate-fade-in ${mine ? "flex-row-reverse" : ""}`}>
      {mine ? <UserAvatar /> : <CompanionAvatar />}
      <div className={`max-w-[85%] md:max-w-[75%] ${dimmed ? "opacity-70" : ""}`}>
        <div
          className={`rounded-2xl px-4 py-3 text-[15px] leading-relaxed md:px-5 ${
            mine
              ? "rounded-br-md bg-forest-50 text-forest-800"
              : "rounded-bl-md border border-cream-200/80 bg-cream-50 text-ink"
          }`}
        >
          <span className="sr-only">{mine ? t("companion.you") : t("companion.panelTitle")}: </span>
          <FormattedText text={content} />
          {time && (
            <p className={`mt-1.5 text-[11px] text-sage-600 ${mine ? "text-right" : ""}`}>
              {new Date(time).toLocaleTimeString(i18n.resolvedLanguage, { hour: "2-digit", minute: "2-digit" })}
            </p>
          )}
        </div>
        {actions && <div className="mt-2">{actions}</div>}
      </div>
    </div>
  );
}

const BULLET = /^\s*(?:[-•*]|\d+[.)])\s+/;

/** Plain text with paragraphs and "- " bullet lines (the only formatting the Companion is asked to use).
 * Consecutive bullet lines become a list; other lines stay paragraphs. */
function FormattedText({ text }: { text: string }) {
  const groups: { list: boolean; lines: string[] }[] = [];
  for (const line of text.trim().split("\n")) {
    const list = BULLET.test(line);
    if (!line.trim()) {
      groups.push({ list: false, lines: [] }); // paragraph break
      continue;
    }
    const last = groups[groups.length - 1];
    if (last && last.list === list && last.lines.length) last.lines.push(line);
    else groups.push({ list, lines: [line] });
  }
  return (
    <div className="space-y-2.5">
      {groups
        .filter((g) => g.lines.length)
        .map((g, i) =>
          g.list ? (
            <ul key={i} className="list-disc space-y-1 pl-5 marker:text-gold-500">
              {g.lines.map((l, j) => (
                <li key={j}>{inline(l.replace(BULLET, ""))}</li>
              ))}
            </ul>
          ) : (
            <p key={i} className="whitespace-pre-line">
              {inline(g.lines.join("\n"))}
            </p>
          ),
        )}
    </div>
  );
}

/** **bold** and *emphasis* only; everything else is rendered as text (no HTML). */
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*\n]+\*\*|\*[^*\s][^*\n]*\*)/g).map((part, i) => {
    if (part.length > 4 && part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-forest-800">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.length > 2 && part.startsWith("*") && part.endsWith("*")) {
      return <em key={i}>{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

function ThinkingBubble() {
  const { t } = useTranslation();
  return (
    <div className="flex items-end gap-3" role="status">
      <CompanionAvatar />
      <div className="flex items-center gap-2.5 rounded-2xl rounded-bl-md border border-cream-200/80 bg-cream-50 px-4 py-3 text-sm text-sage-600">
        <span className="flex gap-1" aria-hidden>
          {[0, 150, 300].map((d) => (
            <span key={d} className="h-1.5 w-1.5 animate-bounce rounded-full bg-gold-500" style={{ animationDelay: `${d}ms` }} />
          ))}
        </span>
        {t("companion.thinking")}
      </div>
    </div>
  );
}

export function ConversationComposer({ onSend, disabled }: { onSend: (text: string) => Promise<boolean>; disabled: boolean }) {
  const { t } = useTranslation();
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  // Grow with the text, up to a few lines.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [text]);

  const submit = () => {
    const value = text.trim();
    if (!value || disabled) return;
    setText("");
    void onSend(value);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="border-t border-cream-200/70 px-4 pb-4 pt-3 md:px-7">
      <div className="flex items-end gap-2 rounded-2xl border border-sage-200 bg-white py-1.5 pl-4 pr-1.5 focus-within:border-forest-600 focus-within:ring-2 focus-within:ring-forest-600/20">
        <textarea
          ref={ref}
          rows={1}
          value={text}
          maxLength={MAX_CHARS}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={t("companion.placeholder")}
          aria-label={t("companion.placeholder")}
          className="max-h-40 flex-1 resize-none bg-transparent py-2 text-[15px] text-ink placeholder:text-sage-600 focus:outline-none"
        />
        <button
          onClick={submit}
          disabled={disabled || !text.trim()}
          aria-label={t("companion.send")}
          className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-forest-700 text-cream-50 transition hover:bg-forest-800 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <SendIcon className="h-[18px] w-[18px]" />
        </button>
      </div>
      <p className="mt-2 hidden px-1 text-[11px] text-sage-600 md:block">
        {t("companion.hint")} · {t("companion.aiNote")}
      </p>
      <p className="mt-2 px-1 text-[11px] text-sage-600 md:hidden">{t("companion.aiNote")}</p>
    </div>
  );
}

function RecentChats({
  conversations,
  activeId,
  onOpen,
  disabled,
}: {
  conversations: ConversationSummary[];
  activeId: number | null;
  onOpen: (id: number) => void;
  disabled: boolean;
}) {
  const { t, i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        disabled={disabled}
        aria-expanded={open}
        aria-label={t("companion.recent")}
        title={t("companion.recent")}
        className="grid h-10 w-10 place-items-center rounded-full text-forest-700 transition hover:bg-forest-50 disabled:opacity-40"
      >
        <HistoryIcon />
      </button>
      {open && (
        <div className="absolute right-0 z-20 mt-2 w-72 rounded-2xl border border-cream-200 bg-white p-2 shadow-card">
          <p className="px-3 pb-1 pt-2 text-[11px] font-semibold uppercase tracking-wider text-sage-600">{t("companion.recent")}</p>
          {conversations.length === 0 ? (
            <p className="px-3 py-3 text-sm text-sage-600">{t("companion.noRecent")}</p>
          ) : (
            <ul className="max-h-72 overflow-y-auto">
              {conversations.map((c) => (
                <li key={c.id}>
                  <button
                    onClick={() => {
                      onOpen(c.id);
                      setOpen(false);
                    }}
                    className={`flex w-full items-center justify-between gap-3 rounded-xl px-3 py-2.5 text-left text-sm transition hover:bg-forest-50 ${
                      c.id === activeId ? "bg-forest-50 font-medium" : ""
                    }`}
                  >
                    <span className="min-w-0">
                      <span className="block truncate text-forest-700">{c.title || t("companion.untitled")}</span>
                      <span className="text-xs text-sage-600">{formatDate(c.updated_at, i18n.resolvedLanguage)}</span>
                    </span>
                    <ChevronIcon className="h-4 w-4 shrink-0 text-sage-600" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

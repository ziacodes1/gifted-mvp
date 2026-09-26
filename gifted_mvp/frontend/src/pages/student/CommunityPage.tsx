import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ecosystemApi } from "../../api/ecosystem";
import hero from "../../assets/ecosystem/community_hero.webp";
import { PhotoHero } from "../../components/PhotoHero";
import { CircleTile, LoadError, PageSkeleton, SectionTitle } from "../../features/ecosystem/components";
import { CalendarIcon, CircleIcon, ExternalIcon, FlagIcon } from "../../features/ecosystem/icons";
import { authorName, ECO_KEYS, initials, timeAgo } from "../../features/ecosystem/lib";
import { QuoteIcon } from "../../features/passport/icons";
import type { CircleCard, CommunityEvent, CommunityOverview, CommunityPost, PostType, ReportReason } from "../../types/ecosystem";
import { formatMonthDay, formatTime, formatWeekday } from "../../utils/date";

const POST_TYPES: PostType[] = ["SHARE", "QUESTION", "IDEA", "ACHIEVEMENT"];
const REASONS: ReportReason[] = ["UNKIND", "UNSAFE", "SPAM", "OTHER"];
const POST_MAX = 1000;

/** /app/community — moderated circles for learners. No DMs, followers, likes or anonymous posts. */
export function CommunityPage() {
  const { t } = useTranslation();
  const qc = useQueryClient();
  const { data, isLoading, isError, refetch } = useQuery({ queryKey: ECO_KEYS.community, queryFn: ecosystemApi.community });
  const update = (next: CommunityOverview) => {
    qc.setQueryData(ECO_KEYS.community, next);
    void qc.invalidateQueries({ queryKey: ECO_KEYS.forYou });
  };
  const membership = useMutation({
    mutationFn: ({ slug, join }: { slug: string; join: boolean }) => (join ? ecosystemApi.join(slug) : ecosystemApi.leave(slug)),
    onSuccess: update,
  });

  if (isLoading) return <PageSkeleton />;
  if (isError || !data) return <LoadError onRetry={() => void refetch()} />;
  const busy = (slug: string) => membership.isPending && membership.variables?.slug === slug;
  const others = data.circles.filter((c) => !c.joined && !data.suggested.some((s) => s.slug === c.slug));

  return (
    <div className="mx-auto max-w-6xl space-y-7">
      <PhotoHero image={hero} eyebrow={t("eco.community.eyebrow")} title={t("eco.community.title")}>
        <p className="mt-3 font-serif text-xl text-forest-800">{t("eco.community.tagline")}</p>
        <p className="mt-2 max-w-xl leading-relaxed text-forest-700">{t("eco.community.subtitle")}</p>
      </PhotoHero>

      {data.suggested.length > 0 && (
        <section className="space-y-4">
          <SectionTitle title={t("eco.community.suggested")} subtitle={data.has_signals ? t("eco.community.suggestedNote") : t("eco.community.suggestedNoSignals")} />
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {data.suggested.map((c) => (
              <CircleTile key={c.slug} c={c} onJoin={() => membership.mutate({ slug: c.slug, join: true })} busy={busy(c.slug)} />
            ))}
          </div>
        </section>
      )}

      <section className="space-y-3">
        <SectionTitle title={t("eco.community.myCircles")} />
        {data.my_circles.length === 0 ? (
          <p className="rounded-2xl bg-white px-5 py-4 text-sm text-sage-600 shadow-soft">{t("eco.community.noCircles")}</p>
        ) : (
          <div className="flex flex-wrap gap-2.5">
            {data.my_circles.map((c) => (
              <MyCircleChip key={c.slug} c={c} busy={busy(c.slug)} onLeave={() => membership.mutate({ slug: c.slug, join: false })} />
            ))}
          </div>
        )}
      </section>

      <div className="grid items-start gap-6 lg:grid-cols-[1.45fr_1fr]">
        <Feed data={data} onUpdate={update} />
        <Events events={data.events} />
      </div>

      {others.length > 0 && (
        <section className="space-y-4">
          <SectionTitle title={t("eco.community.moreCircles")} />
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {others.map((c) => (
              <CircleTile key={c.slug} c={c} compact onJoin={() => membership.mutate({ slug: c.slug, join: true })} busy={busy(c.slug)} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function MyCircleChip({ c, onLeave, busy }: { c: CircleCard; onLeave: () => void; busy: boolean }) {
  const { t } = useTranslation();
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-cream-200 bg-white py-1.5 pl-2 pr-3 text-sm text-forest-700 shadow-soft">
      <span className="grid h-7 w-7 place-items-center rounded-full bg-gold-50 text-gold-600">
        <CircleIcon name={c.icon_key} className="h-4 w-4" />
      </span>
      {c.name}
      <span className="text-xs text-sage-600">· {t("eco.community.members", { count: c.member_count })}</span>
      <button type="button" onClick={onLeave} disabled={busy} className="ml-1 text-xs text-sage-600 hover:text-forest-800 hover:underline">
        {t("eco.community.leave")}
      </button>
    </span>
  );
}

function Feed({ data, onUpdate }: { data: CommunityOverview; onUpdate: (d: CommunityOverview) => void }) {
  const { t } = useTranslation();
  return (
    <section className="card space-y-4" aria-labelledby="feed-title">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-forest-50 text-forest-700">
          <QuoteIcon />
        </span>
        <div>
          <h2 id="feed-title" className="text-xl">
            {t("eco.community.feed")}
          </h2>
          <p className="text-sm text-sage-600">{t("eco.community.feedNote")}</p>
        </div>
      </div>
      <Composer circles={data.my_circles} onPosted={onUpdate} />
      {data.feed.length === 0 ? (
        <p className="text-sm text-sage-600">{t("eco.community.emptyFeed")}</p>
      ) : (
        <ul className="divide-y divide-cream-200">
          {data.feed.map((p) => (
            <PostItem key={p.id} post={p} />
          ))}
        </ul>
      )}
    </section>
  );
}

function Composer({ circles, onPosted }: { circles: CircleCard[]; onPosted: (d: CommunityOverview) => void }) {
  const { t } = useTranslation();
  const [circle, setCircle] = useState("");
  const [type, setType] = useState<PostType>("SHARE");
  const [body, setBody] = useState("");
  const [sent, setSent] = useState(false);
  const target = circle || circles[0]?.slug || "";
  const post = useMutation({
    mutationFn: () => ecosystemApi.post(target, body.trim(), type),
    onSuccess: (d) => {
      setBody("");
      setSent(true);
      onPosted(d);
    },
  });
  if (circles.length === 0) return <p className="rounded-xl bg-cream-50 px-4 py-3 text-sm text-sage-600">{t("eco.community.joinToPost")}</p>;
  const tooShort = body.trim().length < 3;
  const error =
    post.error && isAxiosError(post.error) && post.error.response?.status === 429 ? t("eco.community.tooMany") : post.error ? t("eco.actionError") : null;

  return (
    <form
      className="space-y-2 rounded-2xl bg-cream-50 p-4"
      onSubmit={(e) => {
        e.preventDefault();
        if (!tooShort) post.mutate();
      }}
    >
      <label className="sr-only" htmlFor="post-body">
        {t("eco.community.placeholder")}
      </label>
      <textarea
        id="post-body"
        className="input min-h-[80px] resize-y"
        placeholder={t("eco.community.placeholder")}
        maxLength={POST_MAX}
        value={body}
        onChange={(e) => {
          setBody(e.target.value);
          setSent(false);
        }}
      />
      <div className="flex flex-wrap items-center gap-2">
        <select className="input w-auto py-2" aria-label={t("eco.community.circle")} value={target} onChange={(e) => setCircle(e.target.value)}>
          {circles.map((c) => (
            <option key={c.slug} value={c.slug}>
              {c.name}
            </option>
          ))}
        </select>
        <select className="input w-auto py-2" aria-label={t("eco.community.postType")} value={type} onChange={(e) => setType(e.target.value as PostType)}>
          {POST_TYPES.map((pt) => (
            <option key={pt} value={pt}>
              {t(`eco.community.type.${pt}`)}
            </option>
          ))}
        </select>
        <span className="ml-auto text-xs text-sage-600">
          {body.length}/{POST_MAX}
        </span>
        <button type="submit" className="btn-primary py-2" disabled={tooShort || post.isPending}>
          {t("eco.community.share")}
        </button>
      </div>
      <p className="text-xs text-sage-600">{t("eco.community.guidelines")}</p>
      {sent && <p className="text-sm font-medium text-forest-700" role="status">{t("eco.community.submitted")}</p>}
      {error && <p className="text-sm text-red-700">{error}</p>}
    </form>
  );
}

function PostItem({ post }: { post: CommunityPost }) {
  const { t } = useTranslation();
  const [reporting, setReporting] = useState(false);
  const [reason, setReason] = useState<ReportReason>("UNKIND");
  const [done, setDone] = useState(false);
  const report = useMutation({ mutationFn: () => ecosystemApi.report(post.id, reason), onSuccess: () => setDone(true) });
  const name = authorName(t, post);

  return (
    <li className="py-4">
      <div className="flex gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-forest-50 text-sm font-semibold text-forest-700" aria-hidden>
          {initials(name) || "G"}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
            <span className="font-medium text-forest-800">{name}</span>
            <span className="rounded-full bg-forest-50 px-2 py-0.5 text-xs text-forest-700">{post.circle.name}</span>
            <span className="text-xs text-sage-600">{t(`eco.community.type.${post.post_type}`)}</span>
            <span className="text-xs text-sage-600">· {timeAgo(t, post.created_at)}</span>
            {post.status === "PENDING" && <span className="rounded-full bg-gold-50 px-2 py-0.5 text-xs font-medium text-gold-600">{t("eco.community.pending")}</span>}
            {post.status === "REJECTED" && <span className="rounded-full bg-cream-200 px-2 py-0.5 text-xs text-sage-600">{t("eco.community.rejected")}</span>}
          </div>
          {/* Shown exactly as written: community posts are never translated. */}
          <p className="mt-1 whitespace-pre-line break-words text-sm leading-relaxed text-forest-700">{post.body}</p>
          {!post.mine && post.status === "APPROVED" && (
            <div className="mt-2">
              {done ? (
                <p className="text-xs text-forest-700" role="status">{t("eco.community.reported")}</p>
              ) : reporting ? (
                <div className="flex flex-wrap items-center gap-2">
                  <select className="input w-auto py-1.5 text-xs" aria-label={t("eco.community.reportReason")} value={reason} onChange={(e) => setReason(e.target.value as ReportReason)}>
                    {REASONS.map((r) => (
                      <option key={r} value={r}>
                        {t(`eco.community.reasons.${r}`)}
                      </option>
                    ))}
                  </select>
                  <button type="button" className="rounded-full bg-forest-700 px-3 py-1.5 text-xs font-medium text-cream-50" disabled={report.isPending} onClick={() => report.mutate()}>
                    {t("eco.community.sendReport")}
                  </button>
                  <button type="button" className="text-xs text-sage-600 hover:underline" onClick={() => setReporting(false)}>
                    {t("eco.community.cancel")}
                  </button>
                </div>
              ) : (
                <button type="button" onClick={() => setReporting(true)} className="inline-flex items-center gap-1 text-xs text-sage-600 hover:text-forest-800">
                  <FlagIcon className="h-3.5 w-3.5" /> {t("eco.community.report")}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </li>
  );
}

function Events({ events }: { events: CommunityEvent[] }) {
  const { t, i18n } = useTranslation();
  return (
    <section className="card" aria-labelledby="events-title">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-gold-50 text-gold-600">
          <CalendarIcon className="h-5 w-5" />
        </span>
        <div>
          <h2 id="events-title" className="text-xl">
            {t("eco.community.events")}
          </h2>
          <p className="text-sm text-sage-600">{t("eco.community.eventsNote")}</p>
        </div>
      </div>
      {events.length === 0 ? (
        <p className="mt-4 text-sm text-sage-600">{t("eco.community.noEvents")}</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {events.map((e) => {
            const start = new Date(e.start_at);
            const md = formatMonthDay(start, i18n.language);
            return (
              <li key={e.id} className="flex gap-3 rounded-2xl border border-cream-200/80 p-3">
                <span className="grid w-14 shrink-0 place-items-center rounded-xl bg-[#FFF3E0] py-1.5 text-center leading-tight">
                  <span className="text-[11px] font-semibold uppercase text-gold-600">{md.month}</span>
                  <span className="font-serif text-2xl text-forest-800">{md.day}</span>
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-medium leading-snug text-forest-800">{e.title}</p>
                  <p className="text-xs text-sage-600">
                    {t(`eco.mode.${e.mode}`)}
                    {e.mode !== "ONLINE" && e.location ? ` · ${e.location}` : ""}
                    {e.circle ? ` · ${e.circle.name}` : ""}
                  </p>
                  <p className="text-xs text-sage-600">
                    {formatWeekday(start, i18n.language)}, {formatTime(start)}
                    {e.organization ? ` · ${e.organization.name}` : ""}
                  </p>
                  {e.description && <p className="mt-1 text-xs leading-relaxed text-forest-700">{e.description}</p>}
                  {e.external_url && (
                    <a href={e.external_url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-flex items-center gap-1 text-xs font-medium text-forest-700 hover:underline">
                      {t("eco.community.eventDetails")} <ExternalIcon className="h-3.5 w-3.5" />
                    </a>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

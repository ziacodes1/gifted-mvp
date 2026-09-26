import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState, type ChangeEvent, type KeyboardEvent, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { diaryApi } from "../../api/diary";
import { DiaryBook, Polaroid } from "../../features/diary/DiaryBook";
import { CameraIcon } from "../../features/diary/DiaryHomeSections";
import { DIARY_OVERVIEW_KEY } from "../../features/diary/queries";
import { DaisySprig, FernSketch, MoodFace, Sticker } from "../../features/diary/decor";
import { formatEntryDate, todayISO } from "../../features/diary/format";
import { BackIcon, LockIcon, SparkIcon } from "../../features/passport/icons";
import {
  MAX_PHOTO_BYTES,
  MAX_PHOTOS,
  MAX_TAGS,
  MOODS,
  STICKER_IDS,
  STICKER_SLOTS,
  type DiaryEntry,
  type DiaryPhoto,
  type Mood,
  type PlacedSticker,
  type StickerId,
} from "../../types/diary";

const EMOJI = ["😊", "😄", "🥰", "😌", "🤔", "😴", "😢", "😤", "🎉", "🌱", "🌟", "📚", "🎨", "⚽", "🎵", "❤️"];
const PHOTO_TYPES = ["image/jpeg", "image/png", "image/webp"];
const TILTS = [-3, 2.5, -1.5, 3];

/** Where each sticker slot sits on the open book (decorative, fixed positions). */
const SLOT_POS = [
  "left-[36%] top-[4%]",
  "bottom-[9%] left-[3%]",
  "right-[3%] top-[3%]",
  "right-[1%] top-[46%]",
  "bottom-[8%] right-[7%]",
  "bottom-[10%] left-[40%]",
];

interface Form {
  title: string;
  body: string;
  mood: Mood | "";
  tags: string[];
  stickers: PlacedSticker[];
  entry_date: string;
  companion_message_id?: number;
}

interface QueuedPhoto {
  key: string;
  file: File;
  url: string;
  caption: string;
}

const EMPTY: Form = { title: "", body: "", mood: "", tags: [], stickers: [], entry_date: todayISO() };

function fromEntry(e: DiaryEntry): Form {
  return { title: e.title, body: e.body, mood: e.mood ?? "", tags: e.tags, stickers: e.stickers, entry_date: e.entry_date };
}

/** Remount per entry / draft so moving between pages never carries edits across. */
export function DiaryEntryRoute() {
  const { id } = useParams();
  const [params] = useSearchParams();
  return <DiaryEntryPage key={`${id ?? "new"}:${params.get("from") ?? ""}`} />;
}

/** /app/diary/new (optionally ?from=<companion message id>) and /app/diary/:id.
 * Loads the entry or the Companion draft, then hands a ready form to the editor. */
export function DiaryEntryPage() {
  const { t } = useTranslation();
  const { id: idParam } = useParams();
  const id = idParam ? Number(idParam) : null;
  const [params] = useSearchParams();
  const fromMessage = id === null ? Number(params.get("from")) || null : null;
  const navigate = useNavigate();

  const entry = useQuery({ queryKey: ["diary-entry", id], queryFn: () => diaryApi.entry(id!), enabled: id !== null });
  // "Add to My Diary" from the Companion → prefill from the student's own words (nothing is saved).
  const draft = useQuery({
    queryKey: ["diary-draft", fromMessage],
    queryFn: () => diaryApi.companionDraft(fromMessage!),
    enabled: fromMessage !== null,
    staleTime: 0,
    gcTime: 0,
  });
  const existing = draft.data?.existing_entry_id;

  // This moment was already saved → open that page instead of creating a duplicate.
  useEffect(() => {
    if (existing) navigate(`/app/diary/${existing}`, { replace: true });
  }, [existing, navigate]);

  if (entry.isError || draft.isError) {
    return (
      <div className="mx-auto max-w-3xl card text-center">
        <p className="text-sage-600">{t("diary.editor.loadError")}</p>
        <Link to="/app/diary" className="btn-ghost mt-4">
          {t("diary.editor.back")}
        </Link>
      </div>
    );
  }
  if (id !== null && entry.data) {
    return <DiaryEditor id={id} initial={fromEntry(entry.data)} initialPhotos={entry.data.photos} />;
  }
  if (fromMessage !== null && draft.data && !draft.data.existing_entry_id) {
    const d = (draft.data as Extract<typeof draft.data, { existing_entry_id: null }>).draft;
    const initial = { ...EMPTY, title: d.title, body: d.body, entry_date: d.entry_date, companion_message_id: d.companion_message_id };
    return <DiaryEditor id={null} initial={initial} initialPhotos={[]} />;
  }
  if (id === null && fromMessage === null) {
    return <DiaryEditor id={null} initial={{ ...EMPTY, entry_date: todayISO() }} initialPhotos={[]} />;
  }
  return <div className="mx-auto h-[34rem] max-w-6xl animate-pulse rounded-[26px] bg-forest-50" />;
}

function DiaryEditor({ id, initial, initialPhotos }: { id: number | null; initial: Form; initialPhotos: DiaryPhoto[] }) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const qc = useQueryClient();

  const [form, setForm] = useState<Form>(initial);
  const [photos, setPhotos] = useState<DiaryPhoto[]>(initialPhotos);
  const [queued, setQueued] = useState<QueuedPhoto[]>([]);
  const [panel, setPanel] = useState<"stickers" | "emoji" | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ kind: "error" | "ok"; text: string } | null>(
    (location.state as { saved?: boolean } | null)?.saved ? { kind: "ok", text: t("diary.editor.saved") } : null,
  );
  const [confirmDelete, setConfirmDelete] = useState(false);
  const bodyRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Auto-hide the "saved" note.
  useEffect(() => {
    if (message?.kind !== "ok") return;
    const timer = setTimeout(() => setMessage(null), 2500);
    return () => clearTimeout(timer);
  }, [message]);

  const set = <K extends keyof Form>(key: K, value: Form[K]) => setForm((f) => ({ ...f, [key]: value }));
  const photoCount = photos.length + queued.length;

  /* ---------------------------------------------------------------- photos */

  const onPickPhotos = async (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files ?? []);
    e.target.value = "";
    let room = MAX_PHOTOS - photoCount;
    for (const file of files) {
      if (room <= 0) return setMessage({ kind: "error", text: t("diary.editor.photoErrors.too_many") });
      if (!PHOTO_TYPES.includes(file.type)) return setMessage({ kind: "error", text: t("diary.editor.photoErrors.type") });
      if (file.size > MAX_PHOTO_BYTES) return setMessage({ kind: "error", text: t("diary.editor.photoErrors.size") });
      room -= 1;
      if (id !== null) {
        try {
          const photo = await diaryApi.addPhoto(id, file);
          setPhotos((p) => [...p, photo]);
          invalidate();
        } catch {
          setMessage({ kind: "error", text: t("diary.editor.photoErrors.upload") });
        }
      } else {
        setQueued((q) => [...q, { key: `${file.name}-${file.size}-${q.length}`, file, url: URL.createObjectURL(file), caption: "" }]);
      }
    }
  };

  const removePhoto = async (photoId: number) => {
    await diaryApi.removePhoto(photoId);
    setPhotos((p) => p.filter((x) => x.id !== photoId));
    invalidate();
  };

  /* ---------------------------------------------------------------- stickers / emoji / tags */

  const addSticker = (sid: StickerId) => {
    const used = new Set(form.stickers.map((s) => s.slot));
    const slot = Array.from({ length: STICKER_SLOTS }, (_, i) => i).find((i) => !used.has(i));
    if (slot === undefined) return setMessage({ kind: "error", text: t("diary.editor.stickersFull") });
    set("stickers", [...form.stickers, { id: sid, slot }]);
  };

  const insertEmoji = (emoji: string) => {
    const el = bodyRef.current;
    const start = el?.selectionStart ?? form.body.length;
    const end = el?.selectionEnd ?? form.body.length;
    set("body", form.body.slice(0, start) + emoji + form.body.slice(end));
    requestAnimationFrame(() => {
      el?.focus();
      el?.setSelectionRange(start + emoji.length, start + emoji.length);
    });
  };

  const [tagDraft, setTagDraft] = useState("");
  const onTagKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if ((e.key === "Enter" || e.key === ",") && tagDraft.trim()) {
      e.preventDefault();
      const tag = tagDraft.trim().replace(/^#/, "").slice(0, 24);
      if (tag && form.tags.length < MAX_TAGS && !form.tags.some((x) => x.toLowerCase() === tag.toLowerCase())) {
        set("tags", [...form.tags, tag]);
      }
      setTagDraft("");
    }
  };

  /* ---------------------------------------------------------------- save / delete */

  function invalidate() {
    void qc.invalidateQueries({ queryKey: DIARY_OVERVIEW_KEY });
    void qc.invalidateQueries({ queryKey: ["diary-entries"] });
    void qc.invalidateQueries({ queryKey: ["companion-conversation"] });
  }

  const save = async () => {
    if (saving) return;
    if (!form.title.trim() && !form.body.trim()) return setMessage({ kind: "error", text: t("diary.editor.empty") });
    setSaving(true);
    setMessage(null);
    const values = {
      title: form.title.trim(),
      body: form.body,
      mood: form.mood,
      tags: form.tags,
      stickers: form.stickers,
      entry_date: form.entry_date,
    };
    try {
      if (id !== null) {
        const updated = await diaryApi.update(id, values);
        qc.setQueryData(["diary-entry", id], updated);
        invalidate();
        setMessage({ kind: "ok", text: t("diary.editor.saved") });
      } else {
        const created = await diaryApi.create({ ...values, companion_message_id: form.companion_message_id });
        for (const q of queued) {
          try {
            await diaryApi.addPhoto(created.id, q.file, q.caption);
          } catch {
            /* the entry is saved; a failed photo can be re-added on the entry page */
          }
        }
        invalidate();
        navigate(`/app/diary/${created.id}`, { replace: true, state: { saved: true } });
      }
    } catch {
      setMessage({ kind: "error", text: t("diary.editor.saveError") });
    } finally {
      setSaving(false);
    }
  };

  const remove = async () => {
    if (id === null) return;
    await diaryApi.remove(id);
    qc.removeQueries({ queryKey: ["diary-entry", id] });
    invalidate();
    navigate("/app/diary", { replace: true });
  };

  /* ---------------------------------------------------------------- render */

  const stickerOverlay = form.stickers.map((s) => (
    <button
      key={s.slot}
      type="button"
      onClick={() => set("stickers", form.stickers.filter((x) => x.slot !== s.slot))}
      aria-label={t("diary.editor.removeSticker", { name: t(`diary.stickers.${s.id}`) })}
      className={`absolute z-10 transition hover:scale-110 focus-visible:outline focus-visible:outline-2 focus-visible:outline-forest-600 ${SLOT_POS[s.slot]}`}
    >
      <Sticker id={s.id} className="h-10 w-10 md:h-14 md:w-14" />
    </button>
  ));

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link to="/app/diary" className="inline-flex items-center gap-2 text-sm font-medium text-forest-700 hover:underline">
          <BackIcon /> {t("diary.editor.back")}
        </Link>
        <span className="inline-flex items-center gap-1.5 text-xs text-sage-600">
          <LockIcon className="h-4 w-4" /> {t("diary.editor.privateNote")}
        </span>
      </div>

      {form.companion_message_id && id === null && (
        <div className="flex items-start gap-3 rounded-2xl border border-gold-400/40 bg-gold-50 px-4 py-3 text-sm text-forest-700">
          <SparkIcon className="mt-0.5 h-4 w-4 shrink-0 text-gold-600" />
          <p>{t("diary.editor.companionBanner")}</p>
        </div>
      )}

      <DiaryBook
        overlay={stickerOverlay}
        left={
          <div className="relative flex h-full flex-col pl-6 md:pl-8">
            <DaisySprig className="absolute -left-4 top-0 h-48 w-14 md:-left-7" />
            {/* The handwritten-style date is the visible label; the real date input sits over it. */}
            <label className="relative inline-flex w-fit cursor-pointer items-center gap-1.5 rounded-md text-[13px] font-medium tracking-wide text-[#35507a] focus-within:ring-2 focus-within:ring-forest-600/30">
              <span aria-hidden>{formatEntryDate(form.entry_date, i18n.resolvedLanguage)}</span>
              <span aria-hidden className="text-[10px] text-sage-600">▾</span>
              <input
                type="date"
                value={form.entry_date}
                max={todayISO()}
                onChange={(e) => e.target.value && set("entry_date", e.target.value)}
                onClick={(e) => e.currentTarget.showPicker?.()}
                className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                aria-label={t("diary.editor.date")}
              />
            </label>
            <TitleField
              value={form.title}
              onChange={(v) => set("title", v)}
              placeholder={id === null ? t("diary.editor.newTitle") : t("diary.editor.titlePlaceholder")}
              label={t("diary.editor.titlePlaceholder")}
              onEnter={() => bodyRef.current?.focus()}
            />
            <textarea
              ref={bodyRef}
              value={form.body}
              onChange={(e) => set("body", e.target.value)}
              maxLength={10000}
              placeholder={t("diary.editor.bodyPlaceholder")}
              aria-label={t("diary.editor.bodyPlaceholder")}
              className="diary-lines mt-3 min-h-[20rem] w-full flex-1 resize-none bg-transparent font-hand text-[1.45rem] text-[#2b3f5c] placeholder:text-[#2b3f5c]/35 focus:outline-none md:min-h-[24rem]"
            />
          </div>
        }
        right={
          <div className="relative space-y-6">
            <section aria-label={t("diary.editor.photos")}>
              <div className="grid grid-cols-2 gap-x-5 gap-y-6">
                {photos.map((p, i) => (
                  <Polaroid key={p.id} photoId={p.id} tilt={TILTS[i % 4]} tape={i % 2 ? "rose" : "cream"}>
                    <CaptionInput
                      value={p.caption}
                      onCommit={async (caption) => {
                        const saved = await diaryApi.updatePhoto(p.id, caption);
                        setPhotos((list) => list.map((x) => (x.id === p.id ? saved : x)));
                      }}
                    />
                    <RemoveButton label={t("diary.editor.removePhoto")} onClick={() => void removePhoto(p.id)} />
                  </Polaroid>
                ))}
                {queued.map((q, i) => (
                  <Polaroid key={q.key} src={q.url} tilt={TILTS[(photos.length + i) % 4]}>
                    <CaptionInput value={q.caption} onCommit={(caption) => setQueued((list) => list.map((x) => (x.key === q.key ? { ...x, caption } : x)))} />
                    <RemoveButton label={t("diary.editor.removePhoto")} onClick={() => setQueued((list) => list.filter((x) => x.key !== q.key))} />
                  </Polaroid>
                ))}
                {photoCount < MAX_PHOTOS && (
                  <button
                    type="button"
                    onClick={() => fileRef.current?.click()}
                    className="flex aspect-[4/3.6] flex-col items-center justify-center gap-2 rounded-sm border-2 border-dashed border-[#d9c9a6] text-sm text-forest-700 transition hover:border-forest-600/40 hover:bg-white/50"
                  >
                    <CameraIcon className="h-7 w-7 text-gold-600" />
                    {t("diary.editor.addPhoto")}
                  </button>
                )}
              </div>
              <p className="mt-3 text-[11px] text-sage-600">{t("diary.editor.photoLimit", { count: MAX_PHOTOS })}</p>
              <input ref={fileRef} type="file" accept={PHOTO_TYPES.join(",")} multiple hidden onChange={(e) => void onPickPhotos(e)} data-testid="photo-input" />
            </section>

            <section>
              <p className="font-hand text-2xl text-forest-800">{t("diary.mood.question")}</p>
              <div role="radiogroup" aria-label={t("diary.mood.question")} className="mt-2 flex flex-wrap gap-1.5">
                {MOODS.map((m) => (
                  <button
                    key={m}
                    type="button"
                    role="radio"
                    aria-checked={form.mood === m}
                    aria-label={t(`diary.mood.${m}`)}
                    title={t(`diary.mood.${m}`)}
                    onClick={() => set("mood", form.mood === m ? "" : m)}
                    className={`flex flex-col items-center gap-1 rounded-2xl px-2 py-1.5 text-[11px] transition ${
                      form.mood === m ? "bg-white shadow-soft ring-2 ring-forest-700/60" : "opacity-75 hover:bg-white/60 hover:opacity-100"
                    }`}
                  >
                    <MoodFace mood={m} className="h-9 w-9" />
                    <span className="text-forest-700">{t(`diary.mood.${m}`)}</span>
                  </button>
                ))}
              </div>
            </section>

            <section>
              <p className="font-hand text-2xl text-forest-800">{t("diary.editor.tags")}</p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {form.tags.map((tag) => (
                  <span key={tag} className="inline-flex items-center gap-1 rounded-full bg-[#efe6d2] px-3 py-1 text-sm text-forest-800">
                    #{tag}
                    <button
                      type="button"
                      onClick={() => set("tags", form.tags.filter((x) => x !== tag))}
                      aria-label={t("diary.editor.removeTag", { tag })}
                      className="ml-0.5 text-sage-600 hover:text-forest-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
                {form.tags.length < MAX_TAGS && (
                  <input
                    value={tagDraft}
                    onChange={(e) => setTagDraft(e.target.value)}
                    onKeyDown={onTagKey}
                    placeholder={t("diary.editor.tagPlaceholder")}
                    aria-label={t("diary.editor.tagPlaceholder")}
                    maxLength={24}
                    className="min-w-[12rem] flex-1 border-b border-dashed border-[#d9c9a6] bg-transparent py-1 text-sm text-forest-800 placeholder:text-sage-600 focus:border-forest-600 focus:outline-none"
                  />
                )}
              </div>
            </section>
            <FernSketch className="absolute -bottom-8 right-0 h-16 w-12 opacity-70" />
          </div>
        }
      />

      {/* Toolbar */}
      <div className="relative -mt-2 flex flex-wrap items-center gap-2 rounded-2xl border border-cream-200 bg-white px-3 py-2.5 shadow-soft">
        <ToolButton onClick={() => fileRef.current?.click()} disabled={photoCount >= MAX_PHOTOS}>
          <CameraIcon className="h-5 w-5" /> {t("diary.editor.addPhoto")}
        </ToolButton>
        <ToolButton active={panel === "stickers"} onClick={() => setPanel(panel === "stickers" ? null : "stickers")}>
          <Sticker id="star" className="h-5 w-5" /> {t("diary.editor.stickers")}
        </ToolButton>
        <ToolButton active={panel === "emoji"} onClick={() => setPanel(panel === "emoji" ? null : "emoji")}>
          <span aria-hidden>🙂</span> {t("diary.editor.emoji")}
        </ToolButton>
        <div className="ml-auto flex items-center gap-2">
          {id !== null && (
            <button type="button" onClick={() => setConfirmDelete(true)} className="rounded-full px-3 py-2 text-sm text-sage-600 hover:bg-cream-50 hover:text-forest-800">
              {t("diary.editor.delete")}
            </button>
          )}
          <button type="button" onClick={() => void save()} disabled={saving} className="btn-primary px-6 py-2.5">
            {saving ? t("diary.editor.saving") : t("diary.editor.save")}
          </button>
        </div>

        {panel && (
          <div className="w-full border-t border-cream-200 pt-3">
            {panel === "stickers" ? (
              <>
                <p className="mb-2 text-xs text-sage-600">{t("diary.editor.stickerHint")}</p>
                <div className="flex flex-wrap gap-2">
                  {STICKER_IDS.map((sid) => (
                    <button
                      key={sid}
                      type="button"
                      onClick={() => addSticker(sid)}
                      title={t(`diary.stickers.${sid}`)}
                      aria-label={t(`diary.stickers.${sid}`)}
                      className="grid h-14 w-14 place-items-center rounded-2xl bg-cream-50 transition hover:bg-forest-50"
                    >
                      <Sticker id={sid} className="h-10 w-10" />
                    </button>
                  ))}
                </div>
              </>
            ) : (
              <div className="flex flex-wrap gap-1">
                {EMOJI.map((e) => (
                  <button key={e} type="button" onClick={() => insertEmoji(e)} className="grid h-10 w-10 place-items-center rounded-xl text-xl hover:bg-cream-50" aria-label={e}>
                    {e}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {message && (
        <p
          role={message.kind === "error" ? "alert" : "status"}
          className={`rounded-2xl px-4 py-3 text-sm ${message.kind === "error" ? "border border-gold-400/40 bg-gold-50 text-forest-700" : "bg-forest-700 text-cream-50"}`}
        >
          {message.text}
        </p>
      )}

      {confirmDelete && (
        <div role="alertdialog" aria-modal="true" aria-label={t("diary.editor.deleteConfirm")} className="fixed inset-0 z-50 grid place-items-center bg-forest-900/30 px-4">
          <div className="w-full max-w-sm rounded-3xl bg-white p-6 shadow-card">
            <p className="text-forest-700">{t("diary.editor.deleteConfirm")}</p>
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" onClick={() => setConfirmDelete(false)} className="btn-ghost">
                {t("diary.editor.cancel")}
              </button>
              <button type="button" onClick={() => void remove()} className="btn-primary bg-[#8a3b2e] hover:bg-[#6f2f25]">
                {t("diary.editor.deleteYes")}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/** Auto-growing handwritten title (long titles wrap instead of being cut off). */
function TitleField({ value, onChange, placeholder, label, onEnter }: { value: string; onChange: (v: string) => void; placeholder: string; label: string; onEnter: () => void }) {
  const ref = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [value]);
  return (
    <textarea
      ref={ref}
      rows={1}
      value={value}
      onChange={(e) => onChange(e.target.value.replace(/\n/g, " "))}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          onEnter();
        }
      }}
      maxLength={120}
      placeholder={placeholder}
      aria-label={label}
      className="mt-2 w-full resize-none overflow-hidden bg-transparent font-hand text-[2rem] font-semibold leading-tight text-forest-800 placeholder:text-forest-800/35 focus:outline-none"
    />
  );
}

function ToolButton({ children, onClick, active, disabled }: { children: ReactNode; onClick: () => void; active?: boolean; disabled?: boolean }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-pressed={active}
      className={`inline-flex items-center gap-2 rounded-full px-3.5 py-2 text-sm font-medium transition disabled:opacity-40 ${
        active ? "bg-forest-50 text-forest-800" : "text-forest-700 hover:bg-cream-50"
      }`}
    >
      {children}
    </button>
  );
}

function RemoveButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="absolute -right-2 -top-2 grid h-7 w-7 place-items-center rounded-full bg-white text-sm text-forest-700 shadow-soft ring-1 ring-cream-200 hover:bg-cream-50"
    >
      ×
    </button>
  );
}

function CaptionInput({ value, onCommit }: { value: string; onCommit: (caption: string) => void }) {
  const { t } = useTranslation();
  const [text, setText] = useState(value);
  return (
    <input
      value={text}
      onChange={(e) => setText(e.target.value)}
      onBlur={() => text !== value && onCommit(text.trim())}
      maxLength={120}
      placeholder={t("diary.editor.captionPlaceholder")}
      aria-label={t("diary.editor.captionPlaceholder")}
      className="mt-1.5 w-full bg-transparent text-center font-hand text-lg leading-tight text-forest-800 placeholder:text-sage-600/70 focus:outline-none"
    />
  );
}

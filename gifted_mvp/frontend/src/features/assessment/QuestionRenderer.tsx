import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { PuzzleStimulus, Question, QuestionOption } from "../../types/assessment";
import { CheckIcon } from "../passport/icons";
import { assessmentImage } from "./assessmentAssets";
import { OptionCard } from "./OptionCard";

type Props = { question: Question; selected: number[]; onSelect: (optionId: number) => void };

/** Dispatches on `question.type`: new types only need a layout here, not a new page.
 * Question text comes localized from the server; only the eyebrow is a UI string. */
export function QuestionRenderer(props: Props) {
  const { t } = useTranslation();
  const { question } = props;
  const body = (() => {
    switch (question.type) {
      case "VISUAL_CHOICE":
        return <VisualChoice {...props} />;
      case "STORY_CHOICE":
      case "SCENARIO_CHOICE":
        return <TextChoice {...props} />;
      case "VALUE_TRADEOFF":
        return <Tradeoff {...props} />;
      case "MULTI_SELECT":
        return <MultiSelect {...props} />;
      case "PATTERN_CHOICE":
        return <Puzzle {...props} />;
      default:
        return (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {question.options.map((o) => (
              <OptionCard key={o.id} option={o} selected={props.selected.includes(o.id)} onSelect={() => props.onSelect(o.id)} />
            ))}
          </div>
        );
    }
  })();

  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-widest text-sage-600">{t(`assessment.eyebrow.${question.type}`)}</p>
      {question.content.scenario && (
        <div className="mt-3 rounded-2xl border border-gold-400/30 bg-gold-50 px-5 py-4 font-serif text-lg leading-snug text-forest-700">
          {question.content.scenario}
        </div>
      )}
      <h2 className={`mt-3 text-xl leading-snug text-forest-700 md:text-2xl ${question.type === "PATTERN_CHOICE" ? "text-center" : ""}`}>
        {question.prompt}
      </h2>
      {question.helper_text && (
        <p className={`mt-1 text-sm text-sage-600 ${question.type === "PATTERN_CHOICE" ? "text-center" : ""}`}>
          {question.helper_text}
        </p>
      )}
      <div className="mt-6">{body}</div>
    </div>
  );
}

function selectableClass(selected: boolean) {
  return selected
    ? "border-forest-700 bg-forest-50 shadow-soft ring-1 ring-forest-700"
    : "border-cream-200 bg-white hover:border-forest-600/40 hover:shadow-soft";
}

function Tick({ on }: { on: boolean }) {
  return (
    <span
      className={`grid h-6 w-6 shrink-0 place-items-center rounded-full border transition ${
        on ? "border-forest-700 bg-forest-700 text-cream-50" : "border-sage-200 bg-white text-transparent"
      }`}
    >
      <CheckIcon className="h-3.5 w-3.5" />
    </span>
  );
}

/** Large image cards — the activity, not a category label. */
function VisualChoice({ question, selected, onSelect }: Props) {
  return (
    <div role="radiogroup" className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {question.options.map((o) => {
        const on = selected.includes(o.id);
        const img = assessmentImage(o.image);
        return (
          <button
            key={o.id}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => onSelect(o.id)}
            className={`group overflow-hidden rounded-2xl border text-left transition ${selectableClass(on)}`}
          >
            <div className="relative aspect-[16/10] overflow-hidden bg-cream-100">
              {img && (
                <img src={img} alt="" loading="lazy" className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.03]" />
              )}
              <span className="absolute right-3 top-3">
                <Tick on={on} />
              </span>
            </div>
            <p className="px-4 py-3.5 font-medium leading-snug text-forest-700">{o.label}</p>
          </button>
        );
      })}
    </div>
  );
}

/** Compact text options for stories and situations. */
function TextChoice({ question, selected, onSelect }: Props) {
  return (
    <div role="radiogroup" className="grid gap-2.5">
      {question.options.map((o, i) => {
        const on = selected.includes(o.id);
        return (
          <button
            key={o.id}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => onSelect(o.id)}
            className={`flex items-center gap-4 rounded-2xl border px-4 py-3.5 text-left transition ${selectableClass(on)}`}
          >
            <span
              className={`grid h-8 w-8 shrink-0 place-items-center rounded-full text-sm font-semibold ${
                on ? "bg-forest-700 text-cream-50" : "bg-cream-100 text-forest-700"
              }`}
            >
              {String.fromCharCode(65 + i)}
            </span>
            <span className="text-forest-700">{o.label}</span>
          </button>
        );
      })}
    </div>
  );
}

/** Two contrasting choices with an "or" between them. */
function Tradeoff({ question, selected, onSelect }: Props) {
  const { t } = useTranslation();
  const [a, b] = question.options;
  const card = (o: QuestionOption) => {
    const on = selected.includes(o.id);
    return (
      <button
        type="button"
        role="radio"
        aria-checked={on}
        onClick={() => onSelect(o.id)}
        className={`flex min-h-[9.5rem] flex-col justify-between rounded-3xl border p-6 text-left transition ${selectableClass(on)}`}
      >
        <span className="font-serif text-xl leading-snug text-forest-700">{o.label}</span>
        <span className="mt-4 flex items-center justify-between gap-3 text-sm text-sage-600">
          {o.description}
          <Tick on={on} />
        </span>
      </button>
    );
  };
  return (
    <div role="radiogroup" className="grid items-center gap-3 md:grid-cols-[1fr_auto_1fr]">
      {a && card(a)}
      <span className="mx-auto grid h-10 w-10 place-items-center rounded-full bg-gold-50 font-serif italic text-gold-600">{t("assessment.or")}</span>
      {b && card(b)}
    </div>
  );
}

/** Chips for "what have you tried" — experience, not skill. */
function MultiSelect({ question, selected, onSelect }: Props) {
  return (
    <div className="grid gap-2.5 sm:grid-cols-2">
      {question.options.map((o) => {
        const on = selected.includes(o.id);
        return (
          <button
            key={o.id}
            type="button"
            role="checkbox"
            aria-checked={on}
            onClick={() => onSelect(o.id)}
            className={`flex items-center gap-3 rounded-2xl border px-4 py-3 text-left transition ${selectableClass(on)} ${
              o.content.exclusive ? "sm:col-span-2 border-dashed" : ""
            }`}
          >
            {o.content.icon && <span className="text-lg" aria-hidden>{o.content.icon}</span>}
            <span className="flex-1 text-sm font-medium text-forest-700">{o.label}</span>
            <Tick on={on} />
          </button>
        );
      })}
    </div>
  );
}

function ShapeGlyph({ cells, size = 18 }: { cells: [number, number][]; size?: number }) {
  const rows = Math.max(...cells.map(([r]) => r)) + 1;
  const cols = Math.max(...cells.map(([, c]) => c)) + 1;
  const n = Math.max(rows, cols);
  const offR = (n - rows) / 2;
  const offC = (n - cols) / 2;
  return (
    <svg viewBox={`0 0 ${n * size} ${n * size}`} className="h-full w-full" aria-hidden>
      {cells.map(([r, c]) => (
        <rect
          key={`${r}-${c}`}
          x={(c + offC) * size + 1}
          y={(r + offR) * size + 1}
          width={size - 2}
          height={size - 2}
          rx={3}
          className="fill-forest-700"
        />
      ))}
    </svg>
  );
}

function Stimulus({ stimulus }: { stimulus: PuzzleStimulus }): ReactNode {
  if (stimulus.kind === "sequence") {
    return (
      <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
        {stimulus.items.map((item, i) => (
          <span
            key={i}
            className={`grid h-12 min-w-12 place-items-center rounded-xl px-3 font-serif text-2xl ${
              item === "?" ? "border-2 border-dashed border-gold-500 text-gold-600" : "bg-white text-forest-700 shadow-soft"
            }`}
          >
            {item}
          </span>
        ))}
      </div>
    );
  }
  return (
    <div className="mx-auto h-28 w-28 rounded-2xl bg-white p-3 shadow-soft">
      <ShapeGlyph cells={stimulus.cells} />
    </div>
  );
}

/** Centered puzzle with answer tiles below. Correct answers live only on the server. */
function Puzzle({ question, selected, onSelect }: Props) {
  const { t } = useTranslation();
  const stimulus = question.content.stimulus;
  return (
    <div>
      {stimulus && (
        <div className="rounded-3xl bg-cream-50 px-4 py-8">
          <Stimulus stimulus={stimulus} />
        </div>
      )}
      <div role="radiogroup" className="mx-auto mt-6 grid max-w-xl grid-cols-2 gap-3 sm:grid-cols-4">
        {question.options.map((o) => {
          const on = selected.includes(o.id);
          return (
            <button
              key={o.id}
              type="button"
              role="radio"
              aria-checked={on}
              aria-label={t("assessment.optionLabel", { label: o.label })}
              onClick={() => onSelect(o.id)}
              className={`flex aspect-square flex-col items-center justify-center rounded-2xl border p-3 transition ${selectableClass(on)}`}
            >
              {o.content.cells ? (
                <>
                  <span className="h-16 w-16">
                    <ShapeGlyph cells={o.content.cells} />
                  </span>
                  <span className="mt-2 text-xs font-medium text-sage-600">{o.label}</span>
                </>
              ) : (
                <span className="font-serif text-3xl text-forest-700">{o.label}</span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

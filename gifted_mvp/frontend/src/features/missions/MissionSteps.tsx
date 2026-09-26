import { useTranslation } from "react-i18next";
import type { MissionOption, MissionStep, StepResponse } from "../../types/mission";
import { CheckIcon, LeafIcon, QuoteIcon } from "../passport/icons";
import { selectedList, spent } from "./stepRules";

type StepProps = {
  step: MissionStep;
  value: StepResponse | undefined;
  onChange: (value: StepResponse) => void;
};

/** Dispatch on step.type — new step types only need a renderer here. */
export function StepRenderer(props: StepProps) {
  switch (props.step.type) {
    case "CONTEXT":
      return <ContextStep {...props} />;
    case "MULTI_SELECT":
      return <MultiSelectStep {...props} />;
    case "BUDGET":
      return <BudgetStep {...props} />;
    case "SINGLE_CHOICE":
      return <ChoiceStep {...props} />;
    case "REFLECTION":
      return <ReflectionStep {...props} />;
  }
}

function StepHeading({ step }: { step: MissionStep }) {
  return (
    <div>
      <h2 className="text-2xl leading-snug md:text-3xl">{step.title}</h2>
      {step.prompt && step.type !== "CONTEXT" && (
        <p className="mt-2 max-w-2xl leading-relaxed text-sage-600">{step.prompt}</p>
      )}
    </div>
  );
}

function ContextStep({ step }: StepProps) {
  const { t } = useTranslation();
  const { voices = [], goal } = step.content;
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.25em] text-gold-600">{step.title}</p>
      <p className="mt-3 max-w-3xl font-serif text-2xl leading-snug text-forest-700 md:text-[1.75rem]">{step.prompt}</p>
      <p className="mt-8 text-xs font-medium uppercase tracking-wider text-sage-600">{t("mission.steps.voices")}</p>
      <div className="mt-3 grid gap-4 md:grid-cols-3">
        {voices.map((v) => (
          <figure key={v.quote} className="rounded-2xl border border-cream-200 bg-cream-50 p-5">
            <QuoteIcon className="h-5 w-5 text-gold-400" />
            <blockquote className="mt-2 leading-relaxed text-forest-700">{v.quote}</blockquote>
            <figcaption className="mt-3 text-xs text-sage-600">— {v.who}</figcaption>
          </figure>
        ))}
      </div>
      {goal && (
        <p className="mt-8 flex items-center gap-2 font-medium text-forest-700">
          <LeafIcon className="h-5 w-5 shrink-0" /> {goal}
        </p>
      )}
    </div>
  );
}

function OptionCard({
  option,
  selected,
  disabled,
  onClick,
  aside,
  footer,
  role = "checkbox",
}: {
  option: MissionOption;
  selected: boolean;
  disabled?: boolean;
  onClick: () => void;
  aside?: React.ReactNode;
  footer?: React.ReactNode;
  role?: "checkbox" | "radio";
}) {
  return (
    <button
      type="button"
      role={role}
      aria-checked={selected}
      disabled={disabled}
      onClick={onClick}
      className={`group relative flex w-full items-start gap-4 rounded-2xl border p-5 text-left transition ${
        selected
          ? "border-forest-700 bg-forest-50 shadow-soft"
          : "border-cream-200 bg-white hover:border-forest-600/40 hover:shadow-soft"
      } disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-cream-200 disabled:hover:shadow-none`}
    >
      {option.icon && (
        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-cream-100 text-xl">{option.icon}</span>
      )}
      <span className="min-w-0 flex-1">
        <span className="flex items-start justify-between gap-3">
          <span className="font-medium text-forest-700">{option.label}</span>
          {aside}
        </span>
        {option.description && <span className="mt-1 block text-sm leading-relaxed text-sage-600">{option.description}</span>}
        {footer}
      </span>
      <span
        className={`absolute right-4 top-4 grid h-5 w-5 place-items-center rounded-full border transition ${
          selected ? "border-forest-700 bg-forest-700 text-cream-50" : "border-sage-200 bg-white text-transparent"
        } ${aside ? "hidden" : ""}`}
      >
        <CheckIcon className="h-3 w-3" />
      </span>
    </button>
  );
}

function MultiSelectStep({ step, value, onChange }: StepProps) {
  const { t } = useTranslation();
  const selected = selectedList(value);
  const max = step.content.max ?? Infinity;
  const toggle = (key: string) =>
    onChange({ selected: selected.includes(key) ? selected.filter((k) => k !== key) : [...selected, key] });
  return (
    <div>
      <StepHeading step={step} />
      <p className="mt-4 text-sm font-medium text-forest-700">{t("mission.steps.chosen", { count: selected.length, max })}</p>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        {(step.content.options ?? []).map((o) => (
          <OptionCard
            key={o.key}
            option={o}
            selected={selected.includes(o.key)}
            disabled={!selected.includes(o.key) && selected.length >= max}
            onClick={() => toggle(o.key)}
          />
        ))}
      </div>
    </div>
  );
}

function BudgetStep({ step, value, onChange }: StepProps) {
  const { t } = useTranslation();
  const selected = selectedList(value);
  const budget = step.content.budget ?? 0;
  const used = spent(step, selected);
  const left = budget - used;
  const toggle = (key: string) =>
    onChange({ selected: selected.includes(key) ? selected.filter((k) => k !== key) : [...selected, key] });

  return (
    <div>
      <StepHeading step={step} />
      <div className="mt-5 rounded-2xl border border-cream-200 bg-cream-50 p-4">
        <div className="flex items-baseline justify-between text-sm">
          <span className="font-medium text-forest-700">{t("mission.steps.budgetUsed")}</span>
          <span className="font-serif text-lg text-forest-700">
            {used} <span className="text-sm text-sage-600">/ {t("mission.steps.points", { count: budget })}</span>
          </span>
        </div>
        <div className="mt-2 flex gap-1" aria-hidden>
          {Array.from({ length: budget }, (_, i) => (
            <span key={i} className={`h-2 flex-1 rounded-full ${i < used ? "bg-gold-500" : "bg-cream-200"}`} />
          ))}
        </div>
        <p className="mt-2 text-xs text-sage-600">
          {left > 0 ? t("mission.steps.left", { count: left }) : t("mission.steps.fullyUsed")}
        </p>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {(step.content.options ?? []).map((o) => {
          const isSel = selected.includes(o.key);
          const affordable = isSel || (o.cost ?? 0) <= left;
          return (
            <OptionCard
              key={o.key}
              option={o}
              selected={isSel}
              disabled={!affordable}
              onClick={() => toggle(o.key)}
              aside={
                <span
                  className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                    isSel ? "bg-forest-700 text-cream-50" : "bg-gold-50 text-gold-600"
                  }`}
                >
                  {t("mission.steps.pts", { count: o.cost ?? 0 })}
                </span>
              }
              footer={
                !affordable && (
                  <span className="mt-2 block text-xs text-sage-600">{t("mission.steps.notEnough")}</span>
                )
              }
            />
          );
        })}
      </div>
    </div>
  );
}

function ChoiceStep({ step, value, onChange }: StepProps) {
  const { t } = useTranslation();
  return (
    <div>
      <StepHeading step={step} />
      <div className="mt-5 grid gap-3 md:grid-cols-2" role="radiogroup">
        {(step.content.options ?? []).map((o) => (
          <OptionCard
            key={o.key}
            role="radio"
            option={o}
            selected={value?.selected === o.key}
            onClick={() => onChange({ selected: o.key })}
            footer={
              o.tradeoff && (
                <span className="mt-2 block text-xs font-medium text-gold-600">{t("mission.steps.tradeoff", { text: o.tradeoff })}</span>
              )
            }
          />
        ))}
      </div>
    </div>
  );
}

function ReflectionStep({ step, value, onChange }: StepProps) {
  const { t } = useTranslation();
  return (
    <div>
      <StepHeading step={step} />
      <div className="mt-6 space-y-6">
        {(step.content.fields ?? []).map((f) => {
          const text = String(value?.[f.key] ?? "");
          const max = f.max_length ?? 600;
          return (
            <label key={f.key} className="block">
              <span className="flex items-baseline justify-between gap-3">
                <span className="font-medium text-forest-700">{f.label}</span>
                <span className="shrink-0 text-xs text-sage-600">{f.required ? t("mission.steps.required") : t("mission.steps.optional")}</span>
              </span>
              <textarea
                className="input mt-2 min-h-[7rem] resize-y leading-relaxed"
                placeholder={f.placeholder}
                maxLength={max}
                value={text}
                onChange={(e) => onChange({ ...(value ?? {}), [f.key]: e.target.value })}
              />
              <span className="mt-1 flex justify-between text-xs text-sage-600">
                <span>{f.required && text.trim().length < (f.min_length ?? 1) ? t("mission.steps.atLeast", { count: f.min_length ?? 1 }) : ""}</span>
                <span>
                  {text.length}/{max}
                </span>
              </span>
            </label>
          );
        })}
      </div>
    </div>
  );
}

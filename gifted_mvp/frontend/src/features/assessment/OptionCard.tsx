import type { QuestionOption } from "../../types/assessment";

export function OptionCard({
  option,
  selected,
  onSelect,
}: {
  option: QuestionOption;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={`flex flex-col items-start gap-2 rounded-2xl border p-5 text-left transition ${
        selected
          ? "border-forest-700 bg-forest-50 shadow-soft"
          : "border-sage-200 bg-white hover:border-forest-600/40 hover:bg-forest-50/40"
      }`}
    >
      <span className="text-2xl">{option.icon}</span>
      <span className="font-medium text-forest-700">{option.label}</span>
      {option.description && (
        <span className="text-sm leading-relaxed text-sage-600">{option.description}</span>
      )}
    </button>
  );
}

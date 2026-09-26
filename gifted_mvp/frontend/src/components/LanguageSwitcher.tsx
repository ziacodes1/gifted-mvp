import { useTranslation } from "react-i18next";
import { LANGUAGES, currentLanguage, setLanguage } from "../i18n";

/** Quiet UZ | EN | RU pill. Native names are exposed as tooltip + accessible label. */
export function LanguageSwitcher({ className = "" }: { className?: string }) {
  const { t, i18n } = useTranslation();
  const active = i18n.resolvedLanguage ?? currentLanguage();

  return (
    <div
      role="radiogroup"
      aria-label={t("language.label")}
      className={`inline-flex items-center rounded-full border border-cream-200 bg-cream-50/90 p-0.5 text-[11px] font-semibold tracking-wide ${className}`}
    >
      {LANGUAGES.map((l) => {
        const selected = l.code === active;
        return (
          <button
            key={l.code}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={l.label}
            title={l.label}
            lang={l.code}
            onClick={() => void setLanguage(l.code)}
            className={`rounded-full px-2.5 py-1 transition ${
              selected ? "bg-white text-forest-700 shadow-soft" : "text-sage-600 hover:text-forest-700"
            }`}
          >
            {l.short}
          </button>
        );
      })}
    </div>
  );
}

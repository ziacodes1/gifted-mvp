import { useTranslation } from "react-i18next";
import heroImage from "../../assets/companion/companion_hero.webp";

/** Editorial hero: cream text area on the left, photo on the right (image already fades left). */
export function CompanionHero() {
  const { t } = useTranslation();
  return (
    <div className="relative overflow-hidden rounded-3xl border border-cream-200/80 shadow-card">
      <img src={heroImage} alt="" className="absolute inset-0 h-full w-full object-cover object-[70%_40%]" />
      <div className="absolute inset-0 bg-gradient-to-r from-cream-50 via-cream-50/85 to-cream-50/0 md:via-cream-50/60 md:to-transparent" />
      <div className="relative max-w-2xl p-7 md:px-10 md:py-9">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold-600">{t("companion.eyebrow")}</p>
        <h1 className="mt-3 text-4xl leading-[1.08] md:text-5xl">
          {t("companion.titleA")} <span className="block text-gold-600">{t("companion.titleB")}</span>
        </h1>
        <p className="mt-4 max-w-md leading-relaxed text-forest-700/85">{t("companion.intro")}</p>
      </div>
    </div>
  );
}

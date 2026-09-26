import { useTranslation } from "react-i18next";

/** Minimal placeholder used for foundation routes. Real screens replace these later. */
export function PlaceholderPage({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  const { t } = useTranslation();
  return (
    <div className="mx-auto max-w-3xl">
      <div className="card">
        <p className="text-xs font-medium uppercase tracking-widest text-gold-600">
          Gifted
        </p>
        <h1 className="mt-2 text-2xl">{title}</h1>
        <p className="mt-3 text-sm leading-relaxed text-sage-600">
          {description ?? t("common.comingSoon")}
        </p>
      </div>
    </div>
  );
}

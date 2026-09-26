import type { TFunction } from "i18next";
import type { Spark, SparkAction } from "../../types/today";

export const TODAY_KEY = ["today"] as const;

const factIndex = (key: string) => (key.startsWith("fact_") ? Number(key.slice(5)) : null);

/** Headline text of a spark (a fact is its own headline). */
export function sparkTitle(t: TFunction, key: string): string {
  const i = factIndex(key);
  if (i !== null) return (t("sparks.facts", { returnObjects: true }) as string[])[i] ?? "";
  return t(`sparks.items.${key}.title`);
}

/** What goes into the Companion's message box — in the student's own voice; never auto-sent. */
export function sparkCompanionDraft(t: TFunction, key: string): string {
  if (factIndex(key) !== null) return t("sparks.factCompanion", { fact: sparkTitle(t, key) });
  return t(`sparks.items.${key}.companion`, { defaultValue: sparkTitle(t, key) });
}

/** Known spark keys only (the URL parameter is untrusted). */
export function isSparkKey(t: TFunction, key: string | null): key is string {
  if (!key) return false;
  const i = factIndex(key);
  if (i !== null) return Number.isInteger(i) && i >= 0 && i < (t("sparks.facts", { returnObjects: true }) as string[]).length;
  return /^[a-z_]+$/.test(key) && t(`sparks.items.${key}.title`, { defaultValue: "" }) !== "";
}

/** Where a spark action leads. Nothing is created or sent automatically at the destination. */
export function sparkHref(spark: Spark, action: SparkAction): string | null {
  const q = `spark=${encodeURIComponent(spark.key)}`;
  if (action === "diary") return `/app/diary/new?${q}`;
  if (action === "companion") return `/app/companion?${q}`;
  if (action !== "go") return null;
  switch (spark.route) {
    case "assessment":
      return "/app/assessment";
    case "mission":
      return spark.target ? `/app/missions/${spark.target}` : "/app/missions";
    case "passport":
      return "/app/passport";
    case "diary":
      return `/app/diary/new?${q}`;
    case "companion":
      return `/app/companion?${q}`;
    default:
      return null;
  }
}

// Browsers (e.g. Chrome) ship no Uzbek date names and fall back to "2026 M09 25", so Uzbek
// is formatted from these lists; other languages use Intl.
const UZ_MONTHS = ["yan", "fev", "mar", "apr", "may", "iyn", "iyl", "avg", "sen", "okt", "noy", "dek"];
const UZ_WEEKDAYS = ["Yak", "Du", "Se", "Chor", "Pay", "Ju", "Sha"]; // Sunday first, like Date#getDay

const isUzbek = (language?: string) => (language ?? "").toLowerCase().startsWith("uz");

/** Short date in the UI language (e.g. "25 Sep 2026" / "25 sen 2026" / "25 сент. 2026"). */
export function formatDate(iso: string | Date, language?: string) {
  const date = typeof iso === "string" ? new Date(iso) : iso;
  if (isUzbek(language)) return `${date.getDate()} ${UZ_MONTHS[date.getMonth()]} ${date.getFullYear()}`;
  return date.toLocaleDateString(language, { day: "numeric", month: "short", year: "numeric" });
}

/** Short weekday in the UI language ("Mon" / "Du" / "пн"). */
export function formatWeekday(date: Date, language?: string) {
  if (isUzbek(language)) return UZ_WEEKDAYS[date.getDay()];
  return date.toLocaleDateString(language, { weekday: "short" });
}

/** Month abbreviation + day for date badges ({ month: "Oct", day: "2" }). */
export function formatMonthDay(date: Date, language?: string) {
  const month = isUzbek(language)
    ? UZ_MONTHS[date.getMonth()]
    : date.toLocaleDateString(language, { month: "short" }).replace(".", "");
  return { month, day: String(date.getDate()) };
}

/** 24-hour "16:00" in the viewer's time zone (numeric, so every language reads it). */
export function formatTime(date: Date) {
  return `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

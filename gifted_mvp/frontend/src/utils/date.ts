/** Short date in the UI language (e.g. "25 Sep 2026" / "25 sen 2026" / "25 сент. 2026"). */
export function formatDate(iso: string, language?: string) {
  return new Date(iso).toLocaleDateString(language, { day: "numeric", month: "short", year: "numeric" });
}

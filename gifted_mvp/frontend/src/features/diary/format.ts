import { formatDate, formatWeekday } from "../../utils/date";

/** "2026-09-26" → a local Date (no UTC shift). */
export function parseDay(day: string): Date {
  const [y, m, d] = day.split("-").map(Number);
  return new Date(y, m - 1, d);
}

/** "26 Sep 2026 · Sat" in the UI language. */
export function formatEntryDate(day: string, language?: string): string {
  const date = parseDay(day);
  return `${formatDate(date, language)} · ${formatWeekday(date, language)}`;
}

export function todayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

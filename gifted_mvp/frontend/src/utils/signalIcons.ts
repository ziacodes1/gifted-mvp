// Matches the icons seeded on the corresponding question options.
const ICONS: Record<string, string> = {
  realistic: "\u{1F6E0}",
  investigative: "\u{1F52C}",
  artistic: "\u{1F3A8}",
  social: "\u{1F91D}",
  enterprising: "\u{1F4E3}",
};

export function iconForSignal(key: string): string {
  return ICONS[key] ?? "✨";
}

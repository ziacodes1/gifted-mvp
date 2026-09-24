// Assessment images are bundled; the backend stores only the asset key (file name
// without extension), so content stays server-driven without exposing paths.
const files = import.meta.glob("../../assets/assessment/*.webp", { eager: true, import: "default" }) as Record<
  string,
  string
>;

const byKey: Record<string, string> = Object.fromEntries(
  Object.entries(files).map(([path, url]) => [path.split("/").pop()!.replace(".webp", ""), url]),
);

export function assessmentImage(key: string): string | undefined {
  return key ? byKey[key] : undefined;
}

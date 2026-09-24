/** Minimal placeholder used for foundation routes. Real screens replace these later. */
export function PlaceholderPage({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="mx-auto max-w-3xl">
      <div className="card">
        <p className="text-xs font-medium uppercase tracking-widest text-gold-600">
          Gifted
        </p>
        <h1 className="mt-2 text-2xl">{title}</h1>
        <p className="mt-3 text-sm leading-relaxed text-sage-600">
          {description ?? "This screen is part of the Gifted MVP and is coming soon."}
        </p>
      </div>
    </div>
  );
}

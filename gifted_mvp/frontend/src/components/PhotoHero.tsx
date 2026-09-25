import type { ReactNode } from "react";

/** Photo hero with a cream fade on the left so text stays readable. */
export function PhotoHero({
  image,
  eyebrow,
  title,
  children,
}: {
  image: string;
  eyebrow: string;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="relative overflow-hidden rounded-3xl border border-cream-200/80 shadow-card">
      <img src={image} alt="" className="absolute inset-0 h-full w-full object-cover object-right" />
      <div className="absolute inset-0 bg-gradient-to-r from-cream-50 via-cream-50/90 to-cream-50/0 md:via-cream-50/75" />
      <div className="relative max-w-2xl p-7 md:p-10">
        <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold-600">{eyebrow}</p>
        <h1 className="mt-3 text-4xl leading-tight md:text-5xl">{title}</h1>
        {children}
      </div>
    </div>
  );
}

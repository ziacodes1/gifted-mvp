import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import passportBook from "../../assets/passport/gifted_passport_book.webp";
import heroImage from "../../assets/public/landing_hero_path.webp";
import { ArrowIcon, ChartIcon, CompassIcon, LeafIcon, UserIcon } from "../../features/passport/icons";

const PILLARS: { icon: ReactNode; title: string; text: string; tint: string; iconTint: string }[] = [
  { icon: <LeafIcon className="h-6 w-6" />, title: "Discover", text: "A short assessment surfaces your first interests and signals.", tint: "bg-forest-50/80", iconTint: "text-forest-700" },
  { icon: <CompassIcon className="h-6 w-6" />, title: "Explore", text: "Real-world missions test those signals through action.", tint: "bg-gold-50/90", iconTint: "text-gold-600" },
  { icon: <ChartIcon className="h-6 w-6" />, title: "Grow", text: "Every activity adds evidence — never a fixed label.", tint: "bg-forest-50/80", iconTint: "text-forest-700" },
];

const TRUST = [
  { icon: <UserIcon className="h-4 w-4" />, text: "For curious learners 12–17" },
  { icon: <LeafIcon className="h-4 w-4" />, text: "Built on real evidence" },
  { icon: <CompassIcon className="h-4 w-4" />, text: "No fixed labels" },
];

export function LandingPage() {
  return (
    <div>
      {/* Hero: text column on the left, photographic layer on the right. The cream blend is
          limited to the photo's left/bottom edges so the subject keeps full contrast. */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-y-0 right-0 hidden w-[60%] md:block">
          <img src={heroImage} alt="" className="h-full w-full object-cover object-[45%_35%]" />
          <div className="absolute inset-y-0 left-0 w-[38%] bg-gradient-to-r from-cream via-cream/70 to-transparent" />
          <div className="absolute inset-x-0 bottom-0 h-28 bg-gradient-to-t from-cream to-transparent" />
        </div>

        <div className="relative mx-auto max-w-6xl px-6">
          <div className="max-w-[34rem] pb-8 pt-10 md:pb-40 md:pt-16">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-forest-600">Young people. Brighter tomorrows.</p>
            <h1 className="mt-5 text-5xl leading-[1.02] md:text-[4.25rem]">
              Discover what you could <span className="text-gold-600">become.</span>
            </h1>
            <p className="mt-6 max-w-md text-lg leading-relaxed text-forest-700/85">
              Gifted helps young people discover, test and grow their potential — through short assessments,
              real-world missions and a Passport that evolves with them.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/register" className="btn-primary gap-2 px-7 py-3.5 text-base">
                Get started <ArrowIcon />
              </Link>
              <Link to="/login?as=parent" className="btn-ghost bg-white/80 px-7 py-3.5 text-base">
                I'm a parent
              </Link>
            </div>
            <ul className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-sage-600">
              {TRUST.map((t) => (
                <li key={t.text} className="flex items-center gap-2">
                  <span className="text-forest-600">{t.icon}</span> {t.text}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <img src={heroImage} alt="" className="mx-6 mb-10 aspect-[16/10] w-[calc(100%-3rem)] rounded-3xl object-cover object-[55%_40%] md:hidden" />
      </section>

      {/* Pillars sit over the hero's bottom edge, as in the reference. */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 md:-mt-20">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1fr_1.2fr]">
          {PILLARS.map((p) => (
            <div key={p.title} className={`flex gap-4 rounded-2xl border border-white/70 ${p.tint} p-6 shadow-card backdrop-blur`}>
              <span className={`grid h-14 w-14 shrink-0 place-items-center rounded-full bg-white shadow-soft ${p.iconTint}`}>{p.icon}</span>
              <div>
                <p className="font-serif text-xl text-forest-700">{p.title}</p>
                <p className="mt-1 text-sm leading-relaxed text-sage-600">{p.text}</p>
              </div>
            </div>
          ))}
          <div className="flex items-center gap-4 rounded-2xl border border-white/70 bg-white/90 p-6 shadow-card backdrop-blur">
            <img src={passportBook} alt="" className="w-16 shrink-0 -rotate-3 drop-shadow-lg" />
            <div>
              <p className="font-serif text-xl text-forest-700">Gifted Passport</p>
              <p className="mt-1 text-sm leading-relaxed text-sage-600">Your journey. Your story. Your evidence.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

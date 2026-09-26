import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";
import { missionsApi } from "../../api/missions";
import { ArrowIcon, CheckIcon, ClockIcon, CompassIcon, LeafIcon } from "../../features/passport/icons";
import { WaveSurface } from "../../features/passport/PassportHero";
import type { MissionSummary } from "../../types/mission";

/** /app/missions — one flagship mission for now; each mission adds Passport evidence. */
export function MissionsPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({ queryKey: ["missions"], queryFn: missionsApi.list });

  return (
    <div className="mx-auto max-w-6xl">
      <p className="text-xs font-semibold uppercase tracking-[0.3em] text-gold-600">{t("missions.eyebrow")}</p>
      <h1 className="mt-2 text-4xl leading-tight md:text-5xl">{t("missions.title")}</h1>
      <p className="mt-2 max-w-2xl leading-relaxed text-sage-600">{t("missions.intro")}</p>

      <div className="mt-8 space-y-5">
        {isLoading && <div className="h-64 animate-pulse rounded-3xl bg-white" />}
        {data?.map((m) => <MissionCard key={m.id} mission={m} />)}
        <div className="flex items-start gap-4 rounded-3xl border border-dashed border-sage-200 px-6 py-5">
          <LeafIcon className="mt-0.5 h-5 w-5 shrink-0 text-sage-600" />
          <p className="text-sm leading-relaxed text-sage-600">{t("missions.more")}</p>
        </div>
      </div>
    </div>
  );
}

function MissionCard({ mission }: { mission: MissionSummary }) {
  const { t } = useTranslation();
  const status = mission.my_attempt?.status;
  const cta =
    status === "COMPLETED"
      ? t("passport.next.viewAdded")
      : status === "IN_PROGRESS"
        ? t("passport.next.continue")
        : t("missions.startMissionLower");
  return (
    <WaveSurface>
      <div className="grid gap-6 p-7 md:grid-cols-[1fr_auto] md:items-end md:p-9">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-forest-700 px-3 py-1 text-xs font-medium text-cream-50">{mission.activity_label}</span>
            {status === "COMPLETED" && (
              <span className="inline-flex items-center gap-1 rounded-full bg-forest-50 px-3 py-1 text-xs font-medium text-forest-700">
                <CheckIcon className="h-3 w-3" /> {t("missions.status.completed")}
              </span>
            )}
            {status === "IN_PROGRESS" && (
              <span className="rounded-full bg-gold-50 px-3 py-1 text-xs font-medium text-gold-600">{t("missions.status.inProgress")}</span>
            )}
          </div>
          <h2 className="mt-4 text-3xl leading-tight">{mission.title}</h2>
          <p className="mt-2 max-w-xl leading-relaxed text-forest-700/85">{mission.short_description}</p>
          <div className="mt-5 flex flex-wrap gap-2">
            {mission.focus_areas.map((f) => (
              <span key={f} className="rounded-full border border-cream-200 bg-white/80 px-3 py-1 text-xs text-forest-700">
                {f}
              </span>
            ))}
          </div>
        </div>
        <div className="flex flex-col items-start gap-3 md:items-end">
          <span className="inline-flex items-center gap-4 text-sm text-forest-700">
            <span className="inline-flex items-center gap-1.5">
              <ClockIcon className="h-4 w-4 text-gold-500" /> {mission.time_label}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <CompassIcon className="h-4 w-4 text-gold-500" />
              {t(`missions.difficulty.${mission.difficulty}`)}
            </span>
          </span>
          <Link to={`/app/missions/${mission.slug}`} className="btn-primary gap-2 px-6 py-3">
            {cta} <ArrowIcon />
          </Link>
        </div>
      </div>
    </WaveSurface>
  );
}

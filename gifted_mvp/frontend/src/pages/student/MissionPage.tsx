import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { apiErrorMessage, missionsApi } from "../../api/missions";
import { StepRenderer } from "../../features/missions/MissionSteps";
import { isStepComplete } from "../../features/missions/stepRules";
import { ArrowIcon, BackIcon, CheckIcon, ClockIcon, CompassIcon, LeafIcon, SparkIcon } from "../../features/passport/icons";
import { PassportBook, WaveSurface } from "../../features/passport/PassportHero";
import type { MissionAttempt, MissionDetail, StepResponse } from "../../types/mission";

const DIFFICULTY = { BEGINNER: "Beginner", INTERMEDIATE: "Intermediate" } as const;

/** /app/missions/:slug — intro → steps (server-persisted, refresh-safe) → evidence result. */
export function MissionPage() {
  const { slug = "" } = useParams();
  const queryClient = useQueryClient();

  const detailQuery = useQuery({ queryKey: ["mission", slug], queryFn: () => missionsApi.detail(slug) });
  const attemptId = detailQuery.data?.my_attempt?.id;
  // Side-effect-free GET — safe to refetch/invalidate while mounted.
  const attemptQuery = useQuery({
    queryKey: ["mission-attempt", attemptId],
    queryFn: () => missionsApi.attempt(attemptId!),
    enabled: !!attemptId,
  });

  const startMutation = useMutation({
    mutationFn: () => missionsApi.start(slug),
    onSuccess: (attempt) => {
      queryClient.setQueryData(["mission-attempt", attempt.id], attempt);
      queryClient.setQueryData<MissionDetail>(["mission", slug], (d) =>
        d ? { ...d, my_attempt: { id: attempt.id, status: attempt.status } } : d,
      );
    },
  });

  if (detailQuery.isLoading || (attemptId && attemptQuery.isLoading)) {
    return <div className="grid h-64 place-items-center text-sage-600">Opening your mission…</div>;
  }
  if (detailQuery.isError || !detailQuery.data) {
    return (
      <div className="card mx-auto max-w-lg text-center">
        <p className="text-forest-700">This mission isn't available right now.</p>
        <Link to="/app/missions" className="btn-ghost mt-4">
          Back to missions
        </Link>
      </div>
    );
  }

  const mission = detailQuery.data;
  const attempt = attemptQuery.data;

  return (
    <div className="mx-auto max-w-5xl">
      <Link to="/app/missions" className="inline-flex items-center gap-2 text-sm text-sage-600 hover:text-forest-700">
        <BackIcon /> All missions
      </Link>
      <div className="mt-4">
        {!attempt ? (
          <MissionIntro mission={mission} starting={startMutation.isPending} onStart={() => startMutation.mutate()} />
        ) : attempt.status === "COMPLETED" ? (
          <MissionComplete attempt={attempt} />
        ) : (
          <MissionRunner key={attempt.id} attempt={attempt} />
        )}
      </div>
    </div>
  );
}

function MissionIntro({ mission, starting, onStart }: { mission: MissionDetail; starting: boolean; onStart: () => void }) {
  return (
    <div className="space-y-6">
      <WaveSurface>
        <div className="p-7 md:p-10">
          <p className="text-[11px] font-semibold uppercase tracking-[0.25em] text-gold-600">
            {mission.match === "RECOMMENDED" ? "Recommended for you" : "Suggested exploration"}
          </p>
          <h1 className="mt-3 max-w-2xl text-4xl leading-tight md:text-5xl">{mission.title}</h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-forest-700/85">{mission.short_description}</p>
          <div className="mt-6 flex flex-wrap items-center gap-x-6 gap-y-3 text-sm text-forest-700">
            <span className="inline-flex items-center gap-2">
              <ClockIcon className="h-4 w-4 text-gold-500" /> {mission.time_label}
            </span>
            <span className="inline-flex items-center gap-2">
              <CompassIcon className="h-4 w-4 text-gold-500" /> {mission.activity_label}
            </span>
            <span className="inline-flex items-center gap-2">
              <SparkIcon className="h-4 w-4 text-gold-500" /> {DIFFICULTY[mission.difficulty]}
            </span>
          </div>
          <button className="btn-primary mt-8 gap-2 px-7 py-3 text-base" onClick={onStart} disabled={starting}>
            {starting ? "Starting…" : "Start challenge"} <ArrowIcon />
          </button>
        </div>
      </WaveSurface>

      <div className="grid gap-5 md:grid-cols-[1fr_1.2fr]">
        <div className="card">
          <h2 className="text-lg">What this explores</h2>
          <ul className="mt-4 space-y-3">
            {mission.focus_areas.map((f) => (
              <li key={f} className="flex items-center gap-3 text-forest-700">
                <span className="grid h-8 w-8 place-items-center rounded-full bg-forest-50">
                  <LeafIcon className="h-4 w-4" />
                </span>
                {f}
              </li>
            ))}
          </ul>
          <p className="mt-5 rounded-xl bg-cream-50 px-4 py-3 text-sm leading-relaxed text-sage-600">
            There are no right or wrong answers. Your choices add evidence to your Passport — they are not a test
            score.
          </p>
        </div>
        <div className="card">
          <h2 className="text-lg">What you'll do</h2>
          <ol className="mt-4 space-y-4">
            {mission.intro_steps.map((s, i) => (
              <li key={s.title} className="flex gap-4">
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-forest-700/20 text-sm font-semibold text-forest-700">
                  {i + 1}
                </span>
                <div>
                  <p className="font-medium text-forest-700">{s.title}</p>
                  <p className="text-sm text-sage-600">{s.text}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}

function MissionRunner({ attempt }: { attempt: MissionAttempt }) {
  const queryClient = useQueryClient();
  const steps = attempt.mission.steps;
  const [index, setIndex] = useState(Math.min(attempt.next_step_index, steps.length - 1));
  const [drafts, setDrafts] = useState<Record<string, StepResponse>>(attempt.responses);
  const [error, setError] = useState<string | null>(null);

  const step = steps[index];
  const value = drafts[String(step.id)];
  const isLast = index === steps.length - 1;

  const onDone = (updated: MissionAttempt) => {
    queryClient.setQueryData(["mission-attempt", updated.id], updated);
    queryClient.invalidateQueries({ queryKey: ["passport"] });
    queryClient.invalidateQueries({ queryKey: ["missions"] });
    queryClient.invalidateQueries({ queryKey: ["mission", attempt.mission.slug] });
  };

  const save = useMutation({
    mutationFn: async () => {
      const saved = await missionsApi.answer(attempt.id, step.id, value ?? {});
      return isLast ? missionsApi.complete(attempt.id) : saved;
    },
    onSuccess: (updated) => {
      setError(null);
      if (isLast) onDone(updated);
      else {
        queryClient.setQueryData(["mission-attempt", updated.id], updated);
        setIndex((i) => i + 1);
      }
    },
    onError: (err) => setError(apiErrorMessage(err)),
  });

  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="font-serif text-lg text-forest-700">{attempt.mission.title}</p>
        <p className="text-sm text-sage-600">
          Step {index + 1} of {steps.length}
        </p>
      </div>
      <ol className="mt-3 grid gap-2" style={{ gridTemplateColumns: `repeat(${steps.length}, minmax(0, 1fr))` }}>
        {steps.map((s, i) => (
          <li key={s.id}>
            <div className={`h-1.5 rounded-full ${i < index ? "bg-forest-700" : i === index ? "bg-gold-500" : "bg-cream-200"}`} />
            <p className={`mt-1.5 hidden truncate text-xs sm:block ${i === index ? "font-medium text-forest-700" : "text-sage-600"}`}>
              {s.title}
            </p>
          </li>
        ))}
      </ol>

      <div className="card mt-6 p-6 md:p-10">
        <StepRenderer step={step} value={value} onChange={(v) => setDrafts((d) => ({ ...d, [String(step.id)]: v }))} />
      </div>

      {error && (
        <p role="alert" className="mt-4 rounded-xl bg-gold-50 px-4 py-3 text-sm text-forest-700">
          {error}
        </p>
      )}

      <div className="mt-6 flex items-center justify-between gap-3">
        <button className="btn-ghost" onClick={() => setIndex((i) => i - 1)} disabled={index === 0 || save.isPending}>
          Back
        </button>
        <div className="flex items-center gap-4">
          <span className="hidden text-xs text-sage-600 sm:inline">Your progress is saved as you go.</span>
          <button
            className="btn-primary gap-2 px-6"
            onClick={() => save.mutate()}
            disabled={!isStepComplete(step, value) || save.isPending}
          >
            {save.isPending ? "Saving…" : isLast ? "Complete mission" : step.type === "CONTEXT" ? "Let's begin" : "Continue"}
            {!save.isPending && <ArrowIcon />}
          </button>
        </div>
      </div>
    </div>
  );
}

function MissionComplete({ attempt }: { attempt: MissionAttempt }) {
  const navigate = useNavigate();
  const result = attempt.result;
  return (
    <div className="space-y-6">
      <WaveSurface>
        <div className="grid items-center gap-8 p-7 md:grid-cols-[1fr_auto] md:p-10">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-forest-700 px-3 py-1 text-xs font-medium text-cream-50">
              <CheckIcon className="h-3.5 w-3.5" /> Mission complete
            </span>
            <h1 className="mt-4 max-w-xl text-3xl leading-tight md:text-4xl">New evidence added to your Gifted Passport.</h1>
            <p className="mt-3 max-w-xl leading-relaxed text-forest-700/85">
              This doesn't prove what you're good at — it adds one more piece of evidence about what you explored and how
              you made decisions. Your Passport becomes more informed, not final.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <button className="btn-primary gap-2 px-6 py-3" onClick={() => navigate("/app/passport")}>
                View Updated Passport <ArrowIcon />
              </button>
              <Link to="/app/missions" className="btn-ghost px-6 py-3">
                Back to missions
              </Link>
            </div>
          </div>
          <PassportBook className="mx-auto hidden w-40 rotate-3 md:block" />
        </div>
      </WaveSurface>

      <div className="grid gap-5 md:grid-cols-2">
        <div className="card">
          <h2 className="text-lg">What this activity explored</h2>
          <ul className="mt-4 space-y-3">
            {attempt.mission.focus_areas.map((f) => (
              <li key={f} className="flex items-center gap-3 text-forest-700">
                <span className="grid h-8 w-8 place-items-center rounded-full bg-forest-50">
                  <LeafIcon className="h-4 w-4" />
                </span>
                {f}
              </li>
            ))}
          </ul>
        </div>
        <div className="card">
          <h2 className="text-lg">Evidence added</h2>
          <p className="mt-3 flex items-center justify-between rounded-xl bg-forest-50 px-4 py-3 text-sm font-medium text-forest-700">
            Exploration missions <span className="font-serif text-lg">+1</span>
          </p>
          {result && (
            <ul className="mt-3 divide-y divide-cream-200">
              {result.dimensions.map((d) => (
                <li key={d.key} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                  <span className="text-forest-700">{d.label}</span>
                  <span className="shrink-0 rounded-full bg-gold-50 px-2.5 py-0.5 text-xs font-medium text-gold-600">
                    {d.kind_label}
                  </span>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-3 text-xs text-sage-600">
            Recorded from the choices you made in this mission.
          </p>
        </div>
      </div>
    </div>
  );
}

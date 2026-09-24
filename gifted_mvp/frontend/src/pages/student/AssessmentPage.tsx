import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { assessmentsApi } from "../../api/assessments";
import { QuestionRenderer } from "../../features/assessment/QuestionRenderer";

/** Resumes or starts a session. A completed learner gets `null` (a "completed"
 * screen) instead of silently starting a retake; retakes need `?retake=1`. */
async function fetchOrStartSession(retake: boolean) {
  const assessments = await assessmentsApi.list();
  const assessment = assessments[0];
  if (!assessment) throw new Error("No assessment is available yet.");
  if (assessment.my_latest_session?.status === "COMPLETED" && !retake) return null;
  return assessmentsApi.start(assessment.id);
}

export function AssessmentPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [params] = useSearchParams();
  const retake = params.get("retake") === "1";
  const sessionQuery = useQuery({
    queryKey: ["assessment-active-session", retake],
    queryFn: () => fetchOrStartSession(retake),
  });

  const [responses, setResponses] = useState<Record<string, number[]>>({});
  const [progress, setProgress] = useState(0);
  const [currentIndex, setCurrentIndex] = useState(0);

  // Restore progress from the backend (handles the refresh-mid-assessment case).
  useEffect(() => {
    if (!sessionQuery.data) return;
    setResponses(sessionQuery.data.responses);
    setProgress(sessionQuery.data.progress);
    const firstUnanswered = sessionQuery.data.questions.findIndex(
      (q) => sessionQuery.data!.responses[String(q.id)] === undefined,
    );
    setCurrentIndex(firstUnanswered === -1 ? sessionQuery.data.questions.length - 1 : firstUnanswered);
  }, [sessionQuery.data]);

  const answerMutation = useMutation({
    mutationFn: ({ questionId, optionIds }: { questionId: number; optionIds: number[] }) =>
      assessmentsApi.answer(sessionQuery.data!.id, questionId, optionIds),
    onSuccess: (data) => setProgress(data.progress),
  });

  const completeMutation = useMutation({
    mutationFn: () => assessmentsApi.complete(sessionQuery.data!.id),
    onSuccess: (result) => {
      // Only refresh the dashboard's status list here — "assessment-active-session"
      // has a side-effecting queryFn (it calls start()), so invalidating it while
      // this page is still mounted would immediately re-run it and spawn a stray
      // new session before navigate() below unmounts the page.
      queryClient.invalidateQueries({ queryKey: ["assessments"] });
      queryClient.invalidateQueries({ queryKey: ["passport"] });
      queryClient.invalidateQueries({ queryKey: ["my-signals"] });
      navigate("/app/assessment/result", { state: { result } });
      // Safe now: a completed learner's refetch returns the "completed" screen, never a new session.
      queryClient.removeQueries({ queryKey: ["assessment-active-session"] });
    },
  });

  const questions = sessionQuery.data?.questions ?? [];
  const currentQuestion = questions[currentIndex];
  const totalQuestions = sessionQuery.data?.total_questions ?? 0;
  const allAnswered = useMemo(
    () => questions.length > 0 && questions.every((q) => (responses[String(q.id)] ?? []).length > 0),
    [questions, responses],
  );
  const isLastQuestion = currentIndex === questions.length - 1;

  /** Single-choice types replace the answer; MULTI_SELECT toggles, with an
   * "exclusive" option ("None of these yet") that clears the others. Saved on every change. */
  function selectOption(optionId: number) {
    if (!currentQuestion) return;
    const key = String(currentQuestion.id);
    let next = [optionId];
    if (currentQuestion.type === "MULTI_SELECT") {
      const current = responses[key] ?? [];
      const exclusive = new Set(currentQuestion.options.filter((o) => o.content.exclusive).map((o) => o.id));
      next = current.includes(optionId)
        ? current.filter((id) => id !== optionId)
        : exclusive.has(optionId)
          ? [optionId]
          : [...current.filter((id) => !exclusive.has(id)), optionId];
    }
    setResponses((prev) => ({ ...prev, [key]: next }));
    if (next.length > 0) answerMutation.mutate({ questionId: currentQuestion.id, optionIds: next });
  }

  if (sessionQuery.isLoading) {
    return <div className="grid h-64 place-items-center text-sage-600">Loading your assessment…</div>;
  }

  if (sessionQuery.data === null) return <AssessmentCompleted />;

  if (sessionQuery.isError || !currentQuestion) {
    return (
      <div className="card mx-auto max-w-lg text-center">
        <p className="text-forest-700">This assessment isn't available right now.</p>
        <p className="mt-2 text-sm text-sage-600">Please try again in a moment.</p>
      </div>
    );
  }

  const selected = responses[String(currentQuestion.id)] ?? [];
  const isPuzzle = currentQuestion.type === "PATTERN_CHOICE";

  return (
    <div className="mx-auto max-w-3xl">
      <p className="text-xs font-semibold uppercase tracking-widest text-gold-600">Discovery</p>
      <h1 className="mt-2 text-3xl">What you enjoy, how you think</h1>
      <p className="mt-2 max-w-xl text-sm leading-relaxed text-sage-600">
        Ten short moments — activities, situations, a couple of quick puzzles. About 5 minutes.
      </p>

      <div className="mt-6 flex items-center gap-4">
        <div className="h-2 flex-1 overflow-hidden rounded-full bg-sage-200">
          <div
            className="h-full rounded-full bg-forest-700 transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
        <span className="shrink-0 text-sm text-sage-600">
          Question {currentIndex + 1} of {totalQuestions}
        </span>
      </div>

      <div className="card mt-6 md:p-8">
        <QuestionRenderer question={currentQuestion} selected={selected} onSelect={selectOption} />

        <div className="mt-8 flex items-center justify-between">
          <button
            type="button"
            className="btn-ghost"
            disabled={currentIndex === 0}
            onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
          >
            Back
          </button>

          {isLastQuestion ? (
            <button
              type="button"
              className="btn-primary"
              disabled={!allAnswered || completeMutation.isPending}
              onClick={() => completeMutation.mutate()}
            >
              {completeMutation.isPending ? "Completing…" : "Complete Assessment"}
            </button>
          ) : (
            <button
              type="button"
              className="btn-primary"
              disabled={selected.length === 0}
              onClick={() => setCurrentIndex((i) => Math.min(questions.length - 1, i + 1))}
            >
              Next Question
            </button>
          )}
        </div>
      </div>

      <p className="mt-4 text-center text-xs text-sage-600">
        {isPuzzle
          ? "Just a quick puzzle — one small piece of evidence, never a verdict."
          : "There are no right or wrong answers — choose what feels most true right now."}
      </p>
    </div>
  );
}

function AssessmentCompleted() {
  return (
    <div className="card mx-auto max-w-2xl md:p-10">
      <p className="text-xs font-semibold uppercase tracking-widest text-gold-600">Discovery</p>
      <h1 className="mt-2 text-3xl">You've completed this assessment</h1>
      <p className="mt-3 leading-relaxed text-sage-600">
        Your answers are already part of your emerging profile and Gifted Passport.
      </p>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <Link to="/app/assessment/result" className="btn-primary">
          View Emerging Profile
        </Link>
        <Link to="/app/passport" className="btn-ghost">
          Open my Passport
        </Link>
      </div>
      <p className="mt-6 text-sm text-sage-600">
        Want to see how your answers change?{" "}
        <Link to="/app/assessment?retake=1" className="font-medium text-forest-700 underline-offset-2 hover:underline">
          Retake the assessment
        </Link>
      </p>
    </div>
  );
}

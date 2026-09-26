import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, type ReactNode } from "react";
import { AuthProvider } from "../features/auth/AuthContext";
import i18n from "../i18n";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false, staleTime: 30_000 },
  },
});

// Queries that must not be blindly refetched on a language switch:
// - the active assessment session's queryFn may start() a session, so AssessmentPage
//   reloads it itself via a side-effect-free GET;
// - AI insight keys already include the language, so the new language gets its own entry
//   and the previous one stays cached for when the learner switches back.
const LANGUAGE_SAFE_KEYS = new Set(["assessment-active-session", "profile-insight", "parent-insight"]);

/** Server content (questions, missions, labels, Passport) is localized by the backend,
 * so a language switch refetches it. Progress, answers and scores are unaffected. */
function RefetchOnLanguageChange() {
  useEffect(() => {
    const onChange = () =>
      queryClient.invalidateQueries({ predicate: (q) => !LANGUAGE_SAFE_KEYS.has(String(q.queryKey[0])) });
    i18n.on("languageChanged", onChange);
    return () => i18n.off("languageChanged", onChange);
  }, []);
  return null;
}

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <RefetchOnLanguageChange />
      <AuthProvider>{children}</AuthProvider>
    </QueryClientProvider>
  );
}

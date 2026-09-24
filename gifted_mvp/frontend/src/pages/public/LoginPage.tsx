import { useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import portrait from "../../assets/public/login_portrait.webp";
import { useAuth } from "../../features/auth/AuthContext";
import { HOME_BY_ROLE } from "../../features/auth/RequireAuth";
import { ArrowIcon } from "../../features/passport/icons";

type LoginAs = "student" | "parent";
// Demo accounts are prefilled for the local MVP demo.
const DEMO_EMAIL: Record<LoginAs, string> = { student: "student@gifted.demo", parent: "parent@gifted.demo" };

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const [as, setAs] = useState<LoginAs>(params.get("as") === "parent" ? "parent" : "student");
  const [email, setEmail] = useState(DEMO_EMAIL[as]);
  const [password, setPassword] = useState("demo123");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  function choose(next: LoginAs) {
    setAs(next);
    if (Object.values(DEMO_EMAIL).includes(email)) setEmail(DEMO_EMAIL[next]);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const user = await login(email, password);
      const from = (location.state as { from?: Location })?.from?.pathname;
      navigate(from ?? HOME_BY_ROLE[user.role], { replace: true });
    } catch {
      setError("That email and password don't match. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mx-auto max-w-6xl px-6 pb-6">
      <div className="grid overflow-hidden rounded-3xl border border-cream-200/80 bg-white shadow-card md:grid-cols-[1.05fr_1fr]">
        <div className="relative hidden min-h-[560px] md:block">
          <img src={portrait} alt="" className="absolute inset-0 h-full w-full object-cover object-bottom" />
          <div className="absolute inset-0 bg-gradient-to-b from-cream-50/95 via-cream-50/60 to-transparent" />
          <div className="relative p-10">
            <p className="text-xs font-semibold uppercase tracking-[0.3em] text-forest-600">Young people. Brighter tomorrows.</p>
            <p className="mt-4 font-serif text-4xl leading-tight text-forest-700">
              Discover what you could <span className="text-gold-600">become.</span>
            </p>
          </div>
        </div>

        <form onSubmit={onSubmit} className="flex flex-col justify-center p-8 md:p-12">
          <h1 className="text-3xl">Welcome back</h1>
          <p className="mt-1 text-sage-600">Sign in to continue your journey with Gifted.</p>

          <div role="tablist" className="mt-6 grid grid-cols-2 rounded-full bg-cream-100 p-1 text-sm">
            {(["student", "parent"] as const).map((r) => (
              <button
                key={r}
                type="button"
                role="tab"
                aria-selected={as === r}
                onClick={() => choose(r)}
                className={`rounded-full py-2 font-medium capitalize transition ${
                  as === r ? "bg-white text-forest-700 shadow-soft" : "text-sage-600 hover:text-forest-700"
                }`}
              >
                {r}
              </button>
            ))}
          </div>

          <label className="mt-6 block text-sm font-medium text-forest-700" htmlFor="email">
            Email
          </label>
          <input id="email" className="input mt-1.5" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />

          <label className="mt-4 block text-sm font-medium text-forest-700" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            className="input mt-1.5"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && (
            <p role="alert" className="mt-3 text-sm text-red-700">
              {error}
            </p>
          )}

          <button className="btn-primary mt-6 w-full gap-2 py-3" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"} {!busy && <ArrowIcon />}
          </button>
          <p className="mt-5 text-center text-sm text-sage-600">
            New to Gifted?{" "}
            <Link to="/register" className="font-medium text-forest-700 underline-offset-2 hover:underline">
              Create an account
            </Link>
          </p>
        </form>
      </div>
    </section>
  );
}

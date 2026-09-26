import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router-dom";
import { authApi } from "../../api/auth";
import { useAuth } from "../../features/auth/AuthContext";
import { HOME_BY_ROLE } from "../../features/auth/RequireAuth";
import type { Role } from "../../types/auth";

export function RegisterPage() {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<Exclude<Role, "ADMIN">>("STUDENT");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await authApi.register({ email, password, full_name: fullName, role });
      const user = await login(email, password);
      navigate(HOME_BY_ROLE[user.role], { replace: true });
    } catch {
      setError(t("register.error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="mx-auto grid min-h-[70vh] max-w-md place-items-center px-6">
      <form onSubmit={onSubmit} className="card w-full">
        <h1 className="text-2xl">{t("register.title")}</h1>
        <p className="mt-1 text-sm text-sage-600">{t("register.subtitle")}</p>

        <div className="mt-6 grid grid-cols-2 gap-2">
          {(["STUDENT", "PARENT"] as const).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              className={`rounded-xl border px-4 py-2.5 text-sm transition ${
                role === r
                  ? "border-forest-700 bg-forest-50 font-medium text-forest-700"
                  : "border-sage-200 text-sage-600 hover:border-forest-600/40"
              }`}
            >
              {t(r === "STUDENT" ? "roles.student" : "roles.parent")}
            </button>
          ))}
        </div>

        <label className="mt-4 block text-sm font-medium text-forest-700">{t("auth.fullName")}</label>
        <input className="input mt-1.5" value={fullName} onChange={(e) => setFullName(e.target.value)} />

        <label className="mt-4 block text-sm font-medium text-forest-700">{t("auth.email")}</label>
        <input
          className="input mt-1.5"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <label className="mt-4 block text-sm font-medium text-forest-700">{t("auth.password")}</label>
        <input
          className="input mt-1.5"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}

        <button className="btn-primary mt-6 w-full" disabled={busy}>
          {busy ? t("register.creating") : t("register.submit")}
        </button>
        <p className="mt-4 text-center text-sm text-sage-600">
          {t("register.haveAccount")}{" "}
          <Link to="/login" className="text-forest-700 underline-offset-2 hover:underline">
            {t("public.logIn")}
          </Link>
        </p>
      </form>
    </section>
  );
}

import { useTranslation } from "react-i18next";
import { Link, Outlet } from "react-router-dom";
import { LanguageSwitcher } from "../components/LanguageSwitcher";
import { Logo } from "../components/Logo";

export function PublicLayout() {
  const { t } = useTranslation();
  return (
    <div className="flex min-h-full flex-col">
      <header className="relative z-20 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <Link to="/">
          <Logo variant="light" className="h-14 w-auto md:h-16" />
        </Link>
        <nav className="flex items-center gap-3">
          <LanguageSwitcher className="hidden sm:inline-flex" />
          <Link to="/login" className="btn-ghost">
            {t("public.logIn")}
          </Link>
          <Link to="/register" className="btn-primary">
            {t("public.getStarted")}
          </Link>
        </nav>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="mx-auto w-full max-w-6xl px-6 py-8 text-xs text-sage-600">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span>{t("public.footer")}</span>
          <LanguageSwitcher className="sm:hidden" />
        </div>
      </footer>
    </div>
  );
}

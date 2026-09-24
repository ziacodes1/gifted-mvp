import { Link, Outlet } from "react-router-dom";
import { Logo } from "../components/Logo";

export function PublicLayout() {
  return (
    <div className="flex min-h-full flex-col">
      <header className="relative z-20 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-5">
        <Link to="/">
          <Logo variant="light" className="h-14 w-auto md:h-16" />
        </Link>
        <nav className="flex items-center gap-3">
          <Link to="/login" className="btn-ghost">
            Log in
          </Link>
          <Link to="/register" className="btn-primary">
            Get started
          </Link>
        </nav>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="mx-auto w-full max-w-6xl px-6 py-8 text-xs text-sage-600">
        © Gifted — discover, explore, and develop your potential.
      </footer>
    </div>
  );
}

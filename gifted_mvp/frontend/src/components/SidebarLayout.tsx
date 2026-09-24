import type { ReactNode } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../features/auth/AuthContext";
import { LeafIcon } from "../features/passport/icons";
import { Logo } from "./Logo";

export interface NavItem {
  to: string;
  label: string;
  end?: boolean;
  icon?: ReactNode;
}

/** Shared authenticated shell (student/parent/admin). Light sidebar per the Gifted
 * dashboard references: large logo, icon nav, dark-green active pill. Items differ per role. */
export function SidebarLayout({ items }: { items: NavItem[] }) {
  const { user, logout } = useAuth();

  return (
    <div className="flex h-full bg-cream">
      <aside className="hidden w-[248px] shrink-0 flex-col border-r border-cream-200 bg-cream-50 px-4 pb-5 pt-7 md:flex">
        <Logo variant="light" className="ml-2 h-[76px] w-auto self-start" />
        <nav className="mt-9 flex flex-1 flex-col gap-1.5">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center gap-3.5 rounded-xl px-4 py-3 text-[15px] transition ${
                  isActive
                    ? "bg-forest-700 font-medium text-cream-50 shadow-soft"
                    : "text-forest-700 hover:bg-forest-50"
                }`
              }
            >
              {item.icon && <span className="grid h-5 w-5 place-items-center">{item.icon}</span>}
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="mb-5 rounded-2xl bg-forest-50/70 px-5 py-5">
          <LeafIcon className="h-5 w-5 text-forest-700" />
          <p className="mt-3 font-serif text-xl leading-snug text-forest-700">A brighter future begins with you.</p>
          <div className="mt-3 h-0.5 w-10 rounded-full bg-gold-500" />
        </div>

        <div className="border-t border-cream-200 px-2 pt-4">
          <p className="truncate text-sm font-medium text-forest-700">{user?.full_name || user?.email}</p>
          <p className="text-xs capitalize text-sage-600">{user?.role?.toLowerCase()}</p>
          <button
            onClick={logout}
            className="mt-2 text-xs text-sage-600 underline-offset-2 hover:text-forest-700 hover:underline"
          >
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex-1 overflow-y-auto">
        <main className="mx-auto max-w-6xl px-6 py-8 md:px-10">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

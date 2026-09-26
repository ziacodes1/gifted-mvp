import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthContext";
import type { Role } from "../../types/auth";

const HOME_BY_ROLE: Record<Role, string> = {
  STUDENT: "/app",
  PARENT: "/parent",
  // Admins work in the Django admin (content, rewards, fulfilment) — not in this app.
  ADMIN: "/",
};

/** Role-aware route guard. Pass `roles` to restrict a subtree to given roles. */
export function RequireAuth({ roles }: { roles?: Role[] }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="grid h-full place-items-center text-sage-600">Loading…</div>
    );
  }
  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  if (roles && !roles.includes(user.role)) {
    return <Navigate to={HOME_BY_ROLE[user.role]} replace />;
  }
  return <Outlet />;
}

export { HOME_BY_ROLE };

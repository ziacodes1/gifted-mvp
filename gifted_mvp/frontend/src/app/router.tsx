import { createBrowserRouter, Navigate } from "react-router-dom";
import { PublicLayout } from "../layouts/PublicLayout";
import { StudentLayout } from "../layouts/StudentLayout";
import { ParentLayout } from "../layouts/ParentLayout";
import { AdminLayout } from "../layouts/AdminLayout";
import { RequireAuth } from "../features/auth/RequireAuth";

import { LandingPage } from "../pages/public/LandingPage";
import { LoginPage } from "../pages/public/LoginPage";
import { RegisterPage } from "../pages/public/RegisterPage";
import {
  StudentOverview,
  StudentJourney,
  StudentAssessment,
  AssessmentResultPage,
  StudentPassport,
  StudentMissions,
  StudentMission,
  StudentOpportunities,
  StudentProfile,
} from "../pages/student";
import { ParentHome, ParentInsights } from "../pages/parent";
import { AdminHome } from "../pages/admin";

export const router = createBrowserRouter([
  {
    element: <PublicLayout />,
    children: [
      { path: "/", element: <LandingPage /> },
      { path: "/login", element: <LoginPage /> },
      { path: "/register", element: <RegisterPage /> },
    ],
  },
  {
    element: <RequireAuth roles={["STUDENT"]} />,
    children: [
      {
        path: "/app",
        element: <StudentLayout />,
        children: [
          { index: true, element: <StudentOverview /> },
          { path: "journey", element: <StudentJourney /> },
          { path: "assessment", element: <StudentAssessment /> },
          { path: "assessment/result", element: <AssessmentResultPage /> },
          { path: "passport", element: <StudentPassport /> },
          { path: "missions", element: <StudentMissions /> },
          { path: "missions/:slug", element: <StudentMission /> },
          { path: "opportunities", element: <StudentOpportunities /> },
          { path: "profile", element: <StudentProfile /> },
        ],
      },
    ],
  },
  {
    element: <RequireAuth roles={["PARENT"]} />,
    children: [
      {
        path: "/parent",
        element: <ParentLayout />,
        children: [
          { index: true, element: <ParentHome /> },
          { path: "insights", element: <ParentInsights /> },
        ],
      },
    ],
  },
  {
    element: <RequireAuth roles={["ADMIN"]} />,
    children: [
      {
        path: "/admin",
        element: <AdminLayout />,
        children: [{ index: true, element: <AdminHome /> }],
      },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);

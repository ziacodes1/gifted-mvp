import { createBrowserRouter, Navigate } from "react-router-dom";
import { PublicLayout } from "../layouts/PublicLayout";
import { StudentLayout } from "../layouts/StudentLayout";
import { ParentLayout } from "../layouts/ParentLayout";
import { RequireAuth } from "../features/auth/RequireAuth";

import { LandingPage } from "../pages/public/LandingPage";
import { LoginPage } from "../pages/public/LoginPage";
import { RegisterPage } from "../pages/public/RegisterPage";
import {
  StudentOverview,
  StudentAssessment,
  AssessmentResultPage,
  StudentPassport,
  StudentMissions,
  StudentMission,
  StudentCompanion,
  StudentDiary,
  StudentDiaryEntry,
  StudentRewards,
  StudentResources,
  StudentResource,
  StudentLearningPath,
  StudentOpportunities,
  StudentOpportunity,
  StudentCommunity,
} from "../pages/student";
import { ParentHome, ParentInsights } from "../pages/parent";

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
          { path: "assessment", element: <StudentAssessment /> },
          { path: "assessment/result", element: <AssessmentResultPage /> },
          { path: "passport", element: <StudentPassport /> },
          { path: "missions", element: <StudentMissions /> },
          { path: "missions/:slug", element: <StudentMission /> },
          { path: "companion", element: <StudentCompanion /> },
          { path: "diary", element: <StudentDiary /> },
          { path: "diary/new", element: <StudentDiaryEntry /> },
          { path: "diary/:id", element: <StudentDiaryEntry /> },
          { path: "rewards", element: <StudentRewards /> },
          { path: "resources", element: <StudentResources /> },
          { path: "resources/paths/:slug", element: <StudentLearningPath /> },
          { path: "resources/:slug", element: <StudentResource /> },
          { path: "opportunities", element: <StudentOpportunities /> },
          { path: "opportunities/:slug", element: <StudentOpportunity /> },
          { path: "community", element: <StudentCommunity /> },
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
  { path: "*", element: <Navigate to="/" replace /> },
]);

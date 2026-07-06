import { lazy } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";

import { ProtectedRoute } from "./ProtectedRoute";
import { AuthLayout } from "@/layouts/AuthLayout";
import { DashboardLayout } from "@/layouts/DashboardLayout";

const LoginPage = lazy(() => import("@/features/auth"));
const DashboardPage = lazy(() => import("@/features/dashboard"));
const ProjectsPage = lazy(() => import("@/features/projects"));
const ProjectDetailPage = lazy(() => import("@/features/projects").then((module) => ({ default: module.ProjectDetailPage })));
const KanbanPage = lazy(() => import("@/features/kanban"));
const AiWorkspacePage = lazy(() => import("@/features/ai"));
const GithubIntegrationPage = lazy(() => import("@/features/github"));
const SettingsPage = lazy(() => import("@/features/settings"));

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Navigate to="/login" replace />,
  },
  {
    element: <AuthLayout />,
    children: [
      {
        path: "/login",
        element: <LoginPage />,
      },
    ],
  },
  {
    path: "/app",
    element: <ProtectedRoute />,
    children: [
      {
        element: <DashboardLayout />,
        children: [
          {
            index: true,
            element: <Navigate to="/app/dashboard" replace />,
          },
          {
            path: "dashboard",
            element: <DashboardPage />,
          },
          {
            path: "projects",
            element: <ProjectsPage />,
          },
          {
            path: "projects/:projectId",
            element: <ProjectDetailPage />,
          },
          {
            path: "projects/:projectId/board",
            element: <KanbanPage />,
          },
          {
            path: "ai",
            element: <AiWorkspacePage />,
          },
          {
            path: "integrations/github",
            element: <GithubIntegrationPage />,
          },
          {
            path: "settings",
            element: <SettingsPage />,
          },
        ],
      },
    ],
  },
]);
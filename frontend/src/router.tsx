import { createBrowserRouter } from "react-router-dom";

import { Layout } from "@/components/layout/Layout";
import { Dashboard } from "@/pages/Dashboard";
import { ProjectList } from "@/pages/ProjectList";
import { ProjectDetail } from "@/pages/ProjectDetail";
import { DesignStudio } from "@/pages/DesignStudio";
import { MaterialLibrary } from "@/pages/MaterialLibrary";
import { QuotationView } from "@/pages/QuotationView";

export const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <Layout>
        <Dashboard />
      </Layout>
    ),
  },
  {
    path: "/projects",
    element: (
      <Layout>
        <ProjectList />
      </Layout>
    ),
  },
  {
    path: "/projects/:projectId",
    element: (
      <Layout>
        <ProjectDetail />
      </Layout>
    ),
  },
  {
    path: "/projects/:projectId/design",
    element: (
      <Layout>
        <DesignStudio />
      </Layout>
    ),
  },
  {
    path: "/materials",
    element: (
      <Layout>
        <MaterialLibrary />
      </Layout>
    ),
  },
  {
    path: "/quotations/:quotationId",
    element: (
      <Layout>
        <QuotationView />
      </Layout>
    ),
  },
  {
    path: "/quotations",
    element: (
      <Layout>
        <QuotationView />
      </Layout>
    ),
  },
]);
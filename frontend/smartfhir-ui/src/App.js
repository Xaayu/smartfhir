import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Analytics } from "@vercel/analytics/react";

import LandingPage from "./pages/LandingPage";
import ApiKeyPage from "./pages/ApiKeyPage";
import DocsPage from "./pages/DocsPage";
import ArticlePage from "./pages/ArticlePage";
import ToolsPage from "./pages/ToolsPage";
import AdminPage from "./pages/AdminPage";
import AdminGate from "./pages/AdminGate";
import ProtectedRoute from "./components/ProtectedRoute";
import TerminologyCenterPage from "./pages/TerminologyCenterPage";
import FhirResourcesPage from "./pages/Fhirresourcespage";
import HL7SuitePage from "./pages/hl7suitpage";
import ApiPage from "./pages/ApiPage";

function HomeRoute() {
  const hasApiKey = Boolean(localStorage.getItem("smartfhirApiKey"));
  return hasApiKey ? <Navigate to="/tools" replace /> : <LandingPage />;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Landing */}
      <Route path="/" element={<HomeRoute />} />

      {/* V1 API key collection */}
      <Route path="/api-key" element={<ApiKeyPage />} />

      {/* Docs and knowledge base */}
      <Route path="/docs" element={<DocsPage />} />
      <Route path="/docs/:slug" element={<ArticlePage />} />

      {/* Tools hub */}
      <Route path="/tools" element={<ToolsPage />} />

      {/* Tool-specific dashboards - each protected by API key */}
      <Route
        path="/tools/fhir"
        element={
          <ProtectedRoute>
            <FhirResourcesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tools/hl7-suite"
        element={
          <ProtectedRoute>
            <HL7SuitePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tools/terminology"
        element={
          <ProtectedRoute>
            <TerminologyCenterPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/tools/api"
        element={
          <ProtectedRoute>
            <ApiPage />
          </ProtectedRoute>
        }
      />

      {/* Legacy alias - old bookmarks/links to /dashboard still work */}
      <Route path="/dashboard" element={<Navigate to="/tools/fhir" replace />} />

      {/* Founder analytics - Protected */}
      <Route
        path="/admin"
        element={
          localStorage.getItem("smartfhirAdminToken") ? (
            <AdminPage />
          ) : (
            <AdminGate />
          )
        }
      />

      {/* Unknown Route */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
      <Analytics />
    </BrowserRouter>
  );
}

export default App;
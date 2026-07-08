import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import LandingPage from "./pages/LandingPage";
import ApiKeyPage from "./pages/ApiKeyPage";
import DocsPage from "./pages/DocsPage";
import ArticlePage from "./pages/ArticlePage";
import ToolsPage from "./pages/ToolsPage";
import Dashboard from "./pages/Dashboard";
import AdminPage from "./pages/AdminPage";
import AdminGate from "./pages/AdminGate";
import ProtectedRoute from "./components/ProtectedRoute";
import HL7SuitePage from "./pages/HL7SuitePage";
import TerminologyCenterPage from "./pages/TerminologyCenterPage";

function HomeRoute() {
  const hasApiKey = Boolean(localStorage.getItem("smartfhirApiKey"));
  return hasApiKey ? <Navigate to="/dashboard" replace /> : <LandingPage />;
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
      <Route path="/tools/hl7-suite" element={<HL7SuitePage />} />
      <Route path="/tools/terminology" element={<TerminologyCenterPage />} />

      {/* Dashboard - Protected */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

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
    </BrowserRouter>
  );
}

export default App;

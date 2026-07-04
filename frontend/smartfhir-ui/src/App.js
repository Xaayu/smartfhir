import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Analytics } from "@vercel/analytics/react";

import LandingPage from "./pages/LandingPage";
import ApiKeyPage from "./pages/ApiKeyPage";
import Dashboard from "./pages/Dashboard";
import AdminPage from "./pages/AdminPage";
import AdminGate from "./pages/AdminGate";
import ProtectedRoute from "./components/ProtectedRoute";

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
      <Analytics />
    </BrowserRouter>
  );
}

export default App;

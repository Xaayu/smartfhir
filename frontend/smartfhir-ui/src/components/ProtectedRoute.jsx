/**
 * Protected Route Component
 * Ensures only authenticated users can access certain routes
 */

import React from "react";
import { Navigate } from "react-router-dom";

const hasApiKey = () => Boolean(localStorage.getItem("smartfhirApiKey"));

const ProtectedRoute = ({ children, isAdmin = false }) => {
  // Admin route doesn't require API key
  if (isAdmin) {
    return children;
  }

  // Regular routes require API key
  if (!hasApiKey()) {
    return <Navigate to="/api-key" replace />;
  }

  return children;
};

export default ProtectedRoute;

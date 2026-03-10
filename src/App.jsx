import React from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";

import LandingPage from "./pages/landingpage";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ResumeAnalyzer from "./pages/ResumeAnalyzer";
import JobMatchesPage from "./pages/Jobs";
import Interview from "./pages/Interview";
import FindJobs from "./pages/Find_jobs";
import ResumeBuilder from "./pages/ResumeBuilder";
import SkillRoadmap from "./pages/Roadmap";
import ProfilePage from "./pages/profile";
import LeaderboardPage from "./pages/leaderboard";


const ProtectedRoute = ({ children }) => {
  const user = localStorage.getItem("user");
  const location = useLocation();

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};


function App() {
  return (
    <Routes>

      {/* Landing page */}
      <Route path="/" element={<LandingPage />} />

      {/* Auth pages */}
      <Route path="/login" element={<Login />} />

      {/* Protected routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/resume-analyzer"
        element={
          <ProtectedRoute>
            <ResumeAnalyzer />
          </ProtectedRoute>
        }
      />

      <Route
        path="/jobs"
        element={
          <ProtectedRoute>
            <JobMatchesPage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/interview"
        element={
          <ProtectedRoute>
            <Interview />
          </ProtectedRoute>
        }
      />

      <Route
        path="/find-jobs"
        element={
          <ProtectedRoute>
            <FindJobs />
          </ProtectedRoute>
        }
      />

      <Route
        path="/resume-builder"
        element={
          <ProtectedRoute>
            <ResumeBuilder />
          </ProtectedRoute>
        }
      />

      <Route
        path="/roadmap"
        element={
          <ProtectedRoute>
            <SkillRoadmap />
          </ProtectedRoute>
        }
      />

      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />

      <Route
        path="/leaderboard"
        element={
          <ProtectedRoute>
            <LeaderboardPage />
          </ProtectedRoute>
        }
      />

      {/* Unknown route */}
      <Route path="*" element={<Navigate to="/" replace />} />

    </Routes>
  );
}

export default App;
import React from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";

import LandingPage from "./pages/landingpage.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import ResumeAnalyzer from "./pages/ResumeAnalyzer.jsx";
import Interview from "./pages/Interview.jsx";
import FindJobs from "./pages/Find_jobs.jsx";
import ResumeBuilder from "./pages/ResumeBuilder.jsx";
import SkillRoadmap from "./pages/Roadmap.jsx";
import ProfilePage from "./pages/profile.jsx";
import LeaderboardPage from "./pages/leaderboard.jsx";
import AboutPage from "./components/About.jsx";
import LegalPage from "./components/Policy.jsx";
import PlatformPage from "./components/Platform.jsx";
import ElevateAIChat from "./pages/messages.jsx";
import ElevateFeed from "./pages/feed.jsx";
import SkillRoadmap2 from "./pages/Roadmap2.jsx";

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

      <Route path="/" element={<LandingPage />} />

      <Route path="/login" element={<Login />} />

      <Route path="/about" element={<AboutPage />} />

      <Route path="/legal" element={<LegalPage />} />

      <Route path="/platform" element={<PlatformPage />} />

      <Route path="/profile/:id" element={<ProfilePage />} />

      <Route path="/Roadmap2" element={<SkillRoadmap2 />} />


      <Route
        path="/Dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/ResumeAnalyzer"
        element={
          <ProtectedRoute>
            <ResumeAnalyzer />
          </ProtectedRoute>
        }
      />

      <Route
        path="/Interview"
        element={
          <ProtectedRoute>
            <Interview />
          </ProtectedRoute>
        }
      />

       <Route
        path="/Find_jobs"
        element={
          <ProtectedRoute>
            <FindJobs />
          </ProtectedRoute>
        }
      /> 

      <Route
        path="/ResumeBuilder"
        element={
          <ProtectedRoute>
            <ResumeBuilder />
          </ProtectedRoute>
        }
      />

      <Route
        path="/Roadmap"
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

      <Route
        path="/messages"
        element={
          <ProtectedRoute>
            <ElevateAIChat />
          </ProtectedRoute>
        }
      /> 
      <Route
  path="/feed"
  element={
    <ProtectedRoute>
      <ElevateFeed />
    </ProtectedRoute>
  }
/>
      <Route
  path="/chat/:receiver_id"
  element={
    <ProtectedRoute>
      <ElevateAIChat />
    </ProtectedRoute>
  }
/>
      <Route path="*" element={<Navigate to="/" replace />} />

    </Routes>
  );
}

export default App;
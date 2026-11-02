import React, { useEffect, useState } from 'react';
import { BrowserRouter, Link, Navigate, Route, Routes } from 'react-router-dom';
import LandingPage from './components/landing/LandingPage';
import PlanningForm from './components/planning/PlanningForm';
import InteractiveMap from './components/map/InteractiveMap';
import ItineraryTimeline from './components/itinerary/ItineraryTimeline';
import LoginPage from './components/auth/LoginPage';
import RegisterPage from './components/auth/RegisterPage';
import CommunityFeed from './components/community/CommunityFeed';
import SubmissionForm from './components/community/SubmissionForm';
import { Plan, Site } from './types';
import { clearAuth, getStoredUser, AuthUser } from './api';
import './App.css';

function VirasatApp() {
  const [plan, setPlan] = useState<Plan | null>(null);
  const [sites, setSites] = useState<Site[]>([]);
  const [user, setUser] = useState<AuthUser | null>(getStoredUser);
  useEffect(() => {
    const sync = () => setUser(getStoredUser());
    window.addEventListener('virasat-auth-changed',sync);
    return () => window.removeEventListener('virasat-auth-changed',sync);
  }, []);
  return <>
    <nav className="navbar" aria-label="Main navigation">
      <Link to="/" className="navbar-brand">Virasat</Link>
      <div className="navbar-nav">
        <Link to="/planning" className="nav-link">Plan a walk</Link>
        <Link to="/map" className="nav-link">Map</Link>
        {user ? <><span className="text-sm">{user.email}</span><button onClick={clearAuth}>Sign out</button></> : <Link to="/login" className="nav-link">Sign in</Link>}
      </div>
    </nav>
    <main className="main-content">
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/planning" element={<PlanningForm onPlan={setPlan} onSites={setSites} />} />
        <Route path="/map" element={<InteractiveMap sites={sites} plan={plan} />} />
        <Route path="/itinerary" element={plan ? <div><ItineraryTimeline plan={plan} sites={sites} onPlan={setPlan} /><InteractiveMap plan={plan} sites={sites}/></div> : <Navigate to="/planning" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/community" element={<CommunityFeed />} />
        <Route path="/submission" element={<SubmissionForm />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  </>;
}

export default function App() {
  return <BrowserRouter><VirasatApp /></BrowserRouter>;
}

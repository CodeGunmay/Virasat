import React, { useEffect, useState } from 'react';
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import LandingPage from './components/landing/LandingPage';
import PlanningForm from './components/planning/PlanningForm';
import InteractiveMap from './components/map/InteractiveMap';
import ItineraryTimeline from './components/itinerary/ItineraryTimeline';
import LoginPage from './components/auth/LoginPage';
import RegisterPage from './components/auth/RegisterPage';
import { Plan, Site } from './types';
import { clearAuth, getStoredUser, AuthUser } from './api';
import './App.css';

function VirasatApp() {
  const [plan, setPlan] = useState<Plan | null>(null);
  const [sites, setSites] = useState<Site[]>([]);
  const [user, setUser] = useState<AuthUser | null>(getStoredUser);
  const [menu, setMenu] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setMenu(false);
  }, [location.pathname]);

  useEffect(() => {
    const sync = () => setUser(getStoredUser());
    window.addEventListener('virasat-auth-changed', sync);
    return () => window.removeEventListener('virasat-auth-changed', sync);
  }, []);

  return <>
    <nav className="navbar" aria-label="Main navigation">
      <div className="nav-inner">
        <Link to="/" className="navbar-brand" aria-label="Virasat home"><span className="brand-mark">✦</span> Virasat<span className="brand-dot">.</span></Link>
        <button className="menu-toggle" type="button" aria-expanded={menu} aria-controls="main-links" aria-label={menu ? 'Close menu' : 'Open menu'} onClick={() => setMenu(!menu)}>{menu ? '✕' : '☰'}</button>
        <div className={'navbar-nav ' + (menu ? 'is-open' : '')} id="main-links">
          <Link to="/planning" className="nav-link">Plan a walk</Link>
          {user ? <>
            <span className="nav-email">{user.email}</span>
            <button className="nav-link nav-signin" type="button" onClick={clearAuth}>Sign out</button>
          </> : <Link to="/login" className="nav-link nav-signin">Sign in</Link>}
        </div>
      </div>
    </nav>
    <main id="content" className="main-content">
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/planning" element={<PlanningForm onPlan={setPlan} onSites={setSites} />} />
        <Route path="/map" element={<InteractiveMap sites={sites} plan={plan} />} />
        <Route path="/itinerary" element={plan ? <div className="results-page"><div className="results-header"><span className="eyebrow">YOUR PERSONAL ROUTE</span><h1>Your Ahmedabad heritage walk</h1><p>A little history, a little discovery, entirely at your pace.</p></div><div className="results-grid"><div className="results-list"><ItineraryTimeline plan={plan} sites={sites} onPlan={setPlan} /></div><div className="results-map"><InteractiveMap plan={plan} sites={sites}/></div></div></div> : <Navigate to="/planning" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
    <footer className="site-footer"><span>✦ Virasat</span><span>Heritage walks fitted to your time · Ahmedabad</span><span>Walk thoughtfully. Respect living heritage.</span></footer>
  </>;
}

export default function App() {
  return <BrowserRouter><VirasatApp /></BrowserRouter>;
}

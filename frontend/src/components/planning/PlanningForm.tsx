import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { api } from '../../api';
import { Plan, Site } from '../../types';

interface Props { onPlan: (plan: Plan) => void; onSites: (sites: Site[]) => void }
const categories = [
  { id: 'sultanate', label: 'Sultanate monuments' },
  { id: 'temples_jain', label: 'Temples & Jain derasars' },
  { id: 'pols_living', label: 'Pols & living heritage' },
  { id: 'markets_food', label: 'Markets & food' },
  { id: 'colonial_industrial', label: 'Colonial & industrial' }
];
const times = [60, 120, 180, 240];

export default function PlanningForm({ onPlan, onSites }: Props) {
  const navigate = useNavigate();
  const [sites, setSites] = useState<Site[]>([]);
  const [startId, setStartId] = useState<number | null>(null);
  const [gps, setGps] = useState<{lat: number; lng: number} | null>(null);
  const [duration, setDuration] = useState(180);
  const [custom, setCustom] = useState(false);
  const [pace, setPace] = useState('normal');
  const [interests, setInterests] = useState<string[]>(['sultanate', 'pols_living']);
  const [hidden, setHidden] = useState(0.5);
  const [legCap, setLegCap] = useState(45);
  const [rest, setRest] = useState(0);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState<'sites' | 'plan'>('sites');
  const [loading, setLoading] = useState(false);
  const [sitesLoading, setSitesLoading] = useState(true);
  const [locating, setLocating] = useState(false);

  const load = useCallback(async () => {
    setSitesLoading(true);
    setError('');
    try {
      const { data } = await api.get<{items: Site[]}>('/sites');
      setSites(data.items);
      onSites(data.items);
      setStartId(old => old ?? data.items[0]?.id ?? null);
    } catch {
      setRetry('sites');
      setError('We could not load the starting points. Check your connection and try again.');
    } finally {
      setSitesLoading(false);
    }
  }, [onSites]);

  useEffect(() => { load(); }, [load]);

  function useLocation() {
    if (!navigator.geolocation) {
      setError('Your browser cannot share your location. Choose a landmark instead.');
      return;
    }
    setLocating(true);
    setError('');
    navigator.geolocation.getCurrentPosition(
      pos => { setGps({lat: pos.coords.latitude, lng: pos.coords.longitude}); setLocating(false); },
      () => { setError('Location unavailable or permission denied. You can choose a landmark instead.'); setLocating(false); },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }

  async function generateRoute(event?: React.FormEvent) {
    event?.preventDefault();
    const start = sites.find(s => s.id === startId);
    if (!gps && !start) { setError('Choose a starting landmark or use your location.'); return; }
    setLoading(true);
    setError('');
    try {
      const weights = Object.fromEntries(categories.map(c => [c.id, interests.includes(c.id) ? 2 : 0.2]));
      const { data } = await api.post<Plan>('/plans', {
        start_lat: gps?.lat ?? start!.lat,
        start_lng: gps?.lng ?? start!.lng,
        start_time: new Date().toISOString(),
        duration_minutes: duration,
        interests: weights,
        pace,
        hidden_preference: hidden,
        leg_cap_minutes: legCap,
        rest_minutes: rest
      });
      onPlan(data);
      navigate('/itinerary');
    } catch (err) {
      setRetry('plan');
      setError(axios.isAxiosError(err) && typeof err.response?.data?.detail === 'string'
        ? err.response.data.detail
        : 'We could not create your walk this time. Please retry or adjust your choices.');
    } finally {
      setLoading(false);
    }
  }

  return <div className="planner-page">
    <div className="page-intro"><span className="eyebrow">MADE JUST FOR YOU</span><h1>Let's plan your perfect heritage walk.</h1><p>A few details are all we need to map your next discovery.</p></div>
    <form onSubmit={generateRoute} className="planner-card">
      <div className="form-section"><div className="form-section-head"><span className="field-icon">◷</span><div><h2>How much time do you have?</h2><p>We'll fit the walk into your schedule.</p></div></div>
        <div className="chip-row" role="group" aria-label="Walk duration">
          {times.map(time => <button key={time} type="button" className={'choice-chip ' + (!custom && duration === time ? 'selected' : '')} aria-pressed={!custom && duration === time} onClick={() => {setDuration(time); setCustom(false);}}>{time / 60} hr</button>)}
          <button type="button" className={'choice-chip ' + (custom ? 'selected' : '')} aria-pressed={custom} onClick={() => setCustom(true)}>Custom</button>
        </div>
        {custom && <label className="form-label custom-time">Duration in minutes <input type="number" min="30" max="480" step="15" value={duration} onChange={e => setDuration(Math.max(30, Math.min(480, Number(e.target.value) || 30)))} /></label>}
      </div>
      <div className="form-section"><div className="form-section-head"><span className="field-icon">⌖</span><div><h2>Where shall we begin?</h2><p>Start at a landmark or use your location.</p></div></div>
        {sitesLoading ? <div className="skeleton skeleton-input" role="status" aria-label="Loading landmarks"></div> : <label className="form-label">Starting landmark
          <select value={startId ?? ''} onChange={e => {setStartId(Number(e.target.value)); setGps(null);}} disabled={!sites.length}><option value="" disabled>Choose a landmark</option>{sites.map(site => <option key={site.id} value={site.id}>{site.name}</option>)}</select>
        </label>}
        <button type="button" className={'location-button ' + (gps ? 'location-active' : '')} onClick={useLocation} disabled={locating}>⌖ {locating ? 'Finding your location…' : gps ? 'Using your location ✓' : 'Use my location'}</button>
      </div>
      <div className="form-section"><div className="form-section-head"><span className="field-icon">✧</span><div><h2>What catches your eye?</h2><p>Pick as many as you like.</p></div></div>
        <div className="chip-row interest-row">{categories.map(c => <button type="button" key={c.id} className={'choice-chip interest-chip ' + (interests.includes(c.id) ? 'selected' : '')} aria-pressed={interests.includes(c.id)} onClick={() => setInterests(old => old.includes(c.id) ? old.filter(x => x !== c.id) : [...old, c.id])}>{interests.includes(c.id) ? '✓ ' : '+ '}{c.label}</button>)}</div>
      </div>
      <div className="form-section"><div className="form-section-head"><span className="field-icon">↝</span><div><h2>Your walking pace</h2><p>Make the route comfortable for you.</p></div></div>
        <div className="pace-toggle" role="group" aria-label="Walking pace"><button type="button" className={pace === 'normal' ? 'active' : ''} aria-pressed={pace === 'normal'} onClick={() => setPace('normal')}>Normal pace</button><button type="button" className={pace === 'gentle' ? 'active' : ''} aria-pressed={pace === 'gentle'} onClick={() => setPace('gentle')}>Gentle stroll</button></div>
      </div>
      <details className="advanced-options"><summary>More options <span aria-hidden="true">⌄</span></summary>
        <div className="advanced-fields"><label className="form-label">Maximum walking leg: {legCap} min <input type="range" min="10" max="120" step="5" value={legCap} onChange={e => setLegCap(Number(e.target.value))} /></label>
          <label className="form-label">Rest between stops: {rest} min <input type="range" min="0" max="30" step="5" value={rest} onChange={e => setRest(Number(e.target.value))} /></label>
          <label className="form-label">Hidden gems preference: {Math.round(hidden * 100)}% <input type="range" min="0" max="1" step="0.1" value={hidden} onChange={e => setHidden(Number(e.target.value))} /></label>
        </div>
      </details>
      {error && <div className="notice error-notice" role="alert"><p>{error}</p><button className="btn btn-outline" type="button" onClick={retry === 'sites' ? load : () => generateRoute()}>{retry === 'sites' ? 'Retry loading sites' : 'Try planning again'}</button></div>}
      <button type="submit" className="btn btn-primary planner-submit" disabled={loading || sitesLoading || (!gps && !sites.length)}>{loading ? <><span className="spinner" aria-hidden="true"></span> Finding your best walk…</> : 'Create my heritage walk ↗'}</button>
      {loading && <div className="planner-loading" role="status" aria-label="Building your itinerary"><div className="skeleton skeleton-line"></div><div className="skeleton skeleton-line short"></div><div className="skeleton skeleton-input"></div></div>}
      <p className="form-disclaimer">Walking times are estimates. Check unverified opening hours locally.</p>
    </form>
  </div>;
}

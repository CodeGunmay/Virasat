import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { api } from '../../api';
import { Plan, Site } from '../../types';

interface Props { plan: Plan; sites: Site[]; onPlan: (plan: Plan) => void }
const labels: Record<string, string> = {
  interest_match: 'Matches your interests',
  nearby_fit: 'A good nearby stop',
  locked: 'Kept on your route',
  hours_unverified: 'Check opening hours',
  closed_at_arrival: "Closed when you'd arrive",
  over_budget: 'Not enough time left',
  over_leg_cap: 'Too far for your preferred walk',
  user_skipped: 'You chose to skip',
  already_visited: 'Already visited',
  lower_match: 'Lower match with your interests'
};
const format = (date: Date) => date.toLocaleTimeString('en-IN', {hour: 'numeric', minute: '2-digit', hour12: true, timeZone: 'Asia/Kolkata'});
const getName = (id: number, sites: Site[]) => sites.find(s => s.id === id)?.name || 'Heritage stop ' + id;
const nameList = (ids: number[], sites: Site[]) => ids.map(id => getName(id, sites)).join(', ') || 'None';

export default function ItineraryTimeline({plan, sites, onPlan}: Props) {
  const [minutes, setMinutes] = useState(90);
  const [visited, setVisited] = useState<number[]>([]);
  const [skipped, setSkipped] = useState<number[]>([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [positionSite, setPositionSite] = useState<number | null>(null);
  const [gps, setGps] = useState<{lat: number; lng: number} | null>(null);
  const [change, setChange] = useState<{before: number; after: number; added: number[]; removed: number[]; reordered: number[]} | null>(null);

  useEffect(() => { setVisited([]); setSkipped([]); }, [plan]);

  const finish = new Date(plan.finish_time);
  const start = new Date(finish.getTime() - plan.total_duration_minutes * 60000);
  let elapsed = 0;
  const rows = plan.stops.map((stop, i) => {
    elapsed += stop.walking_minutes + (i ? 0 : 0);
    const arrive = new Date(start.getTime() + elapsed * 60000);
    elapsed += stop.visit_minutes;
    const leave = new Date(start.getTime() + elapsed * 60000);
    return {stop, arrive, leave, index: i};
  });
  const excluded = plan.reasons.filter(item => item.included !== true);
  const allowedReasons = ['closed_at_arrival', 'over_budget', 'over_leg_cap', 'user_skipped', 'already_visited'];

  function useLocation() {
    if (!navigator.geolocation) {setError('Location unavailable. Select a nearby landmark.'); return;}
    navigator.geolocation.getCurrentPosition(
      pos => {setGps({lat: pos.coords.latitude, lng: pos.coords.longitude}); setError('');},
      () => setError('Location unavailable or denied. Choose a landmark instead.'),
      {enableHighAccuracy: true, timeout: 10000}
    );
  }

  async function replan() {
    setBusy(true);
    setError('');
    const first = sites.find(s => s.id === positionSite) || sites.find(s => s.id === plan.stops[0]?.site_id);
    if (!gps && !first) {setError('Choose a current location first.'); setBusy(false); return;}
    try {
      const {data} = await api.post<Plan & {diff?: {added: number[]; removed: number[]; reordered: number[]}}>('/plans/replan', {
        current_lat: gps?.lat ?? first!.lat,
        current_lng: gps?.lng ?? first!.lng,
        current_time: new Date().toISOString(),
        new_duration: minutes,
        visited_ids: visited,
        skipped_ids: skipped,
        locked_ids: [],
        previous_stop_ids: plan.stops.map(s => s.site_id)
      });
      const oldIds = plan.stops.map(s => s.site_id);
      const nextIds = data.stops.map(s => s.site_id);
      setChange({
        before: oldIds.length, after: nextIds.length,
        added: data.diff?.added ?? nextIds.filter(id => !oldIds.includes(id)),
        removed: data.diff?.removed ?? oldIds.filter(id => !nextIds.includes(id) && !visited.includes(id)),
        reordered: data.diff?.reordered ?? []
      });
      onPlan(data);
    } catch (err) {
      setError(axios.isAxiosError(err) && typeof err.response?.data?.detail === 'string' ? err.response.data.detail : 'Could not update your walk. Try again or choose another landmark.');
    } finally {setBusy(false);}
  }

  return <section aria-label="Your planned itinerary">
    <div className="summary-grid">
      <div><span>STOPS</span><strong>{plan.stops.length}</strong></div>
      <div><span>TOTAL TIME</span><strong>{Math.round(plan.total_duration_minutes)} <small>min</small></strong></div>
      <div><span>WALKING</span><strong>{Math.round(plan.walking_minutes)} <small>min</small></strong></div>
      <div><span>FINISH BY</span><strong>{format(finish)}</strong></div>
    </div>

    <div className="itinerary-heading"><div><span className="eyebrow">YOUR ROUTE AT A GLANCE</span><h2>Stop by stop</h2></div><span className="subtle-pill">✦ Curated for you</span></div>
    {!plan.stops.length && <div className="empty-route"><span className="empty-symbol">⌁</span><h3>No walk fits these choices yet</h3><p>Try a longer time window or another starting point. A few small changes can open up more places.</p><a className="btn btn-primary" href="/planning">Adjust my walk</a></div>}
    <ol className="stop-list">
      {rows.map(({stop, arrive, leave, index}) => <li className="stop-card" key={stop.site_id + '-' + index}>
        <div className="stop-track"><span className="stop-number">{index + 1}</span><span className="stop-line"></span></div>
        <div className="stop-content"><div className="stop-top"><span className="stop-kicker">STOP {String(index + 1).padStart(2, '0')}</span><span className="stop-time">{format(arrive)} – {format(leave)}</span></div>
          <h3>{getName(stop.site_id, sites)}</h3>
          <div className="stop-metrics"><span>↝ {Math.round(stop.walking_minutes)} min walk</span><span>◷ {stop.visit_minutes} min here</span></div>
          <div className="reason-tags">{(stop.reason_codes?.length ? stop.reason_codes : [stop.reason]).map(code => <span className="reason-tag" key={code}>{labels[code] || 'Fits your route'}</span>)}</div>
          <div className="stop-actions"><label><input type="checkbox" checked={visited.includes(stop.site_id)} onChange={e => setVisited(old => e.target.checked ? [...old, stop.site_id] : old.filter(id => id !== stop.site_id))}/> Visited</label><label><input type="checkbox" checked={skipped.includes(stop.site_id)} onChange={e => setSkipped(old => e.target.checked ? [...old, stop.site_id] : old.filter(id => id !== stop.site_id))}/> Skip on re-plan</label></div>
        </div>
      </li>)}
    </ol>

    <details className="why-panel" open><summary><span>✧ Why these stops?</span><span className="details-hint">How we shaped your route</span></summary>
      <div className="why-content"><p>We balance your interests, travel time and available visiting hours. Places that don't fit are listed below.</p>
        {excluded.length ? <ul className="excluded-list">{excluded.slice(0, 12).map((item, i) => {
          const id = Number(item.site_id);
          const code = String(item.reason || '');
          return <li key={id + '-' + i}><strong>{getName(id, sites)}</strong><span>{labels[code] || (allowedReasons.includes(code) ? 'Does not fit this walk' : 'Lower match with your interests')}</span></li>;
        })}</ul> : <p className="positive-note">Every eligible place considered fits your choices.</p>}
        <p className="caution-text">Estimated walking routes are approximate. Unverified opening hours should be confirmed locally.</p>
      </div>
    </details>

    <section className="replan-panel" aria-labelledby="replan-title">
      <span className="eyebrow">PLANS CAN CHANGE</span><h2 id="replan-title">Take a detour. We'll adapt.</h2><p>Mark visited or skipped stops above, choose where you are, and get a refreshed route.</p>
      <label className="form-label">Where are you now?
        <select value={positionSite ?? plan.stops[0]?.site_id ?? ''} onChange={e => {setPositionSite(Number(e.target.value)); setGps(null);}}>
          {sites.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
      </label>
      <button className="location-button" type="button" onClick={useLocation}>⌖ {gps ? 'Current location selected ✓' : 'Use my location'}</button>
      <label className="form-label replan-time">Time remaining: <strong>{minutes} minutes</strong><input type="range" min="30" max="360" step="15" value={minutes} onChange={e => setMinutes(Number(e.target.value))}/></label>
      <button className="btn btn-primary" type="button" disabled={busy} onClick={replan}>{busy ? <><span className="spinner"></span> Re-planning…</> : 'Re-plan my walk ↗'}</button>
      {error && <div className="notice error-notice" role="alert">{error} <button className="btn btn-outline" onClick={replan} disabled={busy}>Try again</button></div>}
      {change && <div className="change-card" role="status"><h3>Here's what changed</h3><div className="change-counts"><div><span>BEFORE</span><strong>{change.before} stops</strong></div><span aria-hidden="true">→</span><div><span>AFTER</span><strong>{change.after} stops</strong></div></div><p><strong>Added:</strong> {nameList(change.added, sites)}</p><p><strong>Removed:</strong> {nameList(change.removed, sites)}</p><p><strong>Reordered:</strong> {nameList(change.reordered, sites)}</p></div>}
    </section>
  </section>;
}

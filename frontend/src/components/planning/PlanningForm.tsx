import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Plan, Site } from '../../types';

interface Props { onPlan: (plan: Plan) => void; onSites: (sites: Site[]) => void }
const API = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const categories = ['sultanate', 'temples_jain', 'pols_living', 'markets_food', 'colonial_industrial'];

export default function PlanningForm({ onPlan, onSites }: Props) {
  const navigate = useNavigate();
  const [sites, setSites] = useState<Site[]>([]);
  const [startId, setStartId] = useState<number | null>(null);
  const [duration, setDuration] = useState(180);
  const [pace, setPace] = useState('normal');
  const [interests, setInterests] = useState<string[]>(['sultanate', 'pols_living']);
  const [hidden, setHidden] = useState(0.5);
  const [legCap, setLegCap] = useState(45);
  const [rest, setRest] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios.get<{items: Site[]}>(`${API}/sites`).then(({data}) => {
      setSites(data.items);
      onSites(data.items);
      if (data.items.length) setStartId(data.items[0].id);
    }).catch(() => setError('Could not load heritage sites. Check that the backend is running.'));
  }, [onSites]);

  async function generateRoute() {
    const start = sites.find(s => s.id === startId);
    if (!start) { setError('Select a starting point.'); return; }
    setLoading(true); setError('');
    try {
      const weights = Object.fromEntries(categories.map(c => [c, interests.includes(c) ? 2 : 0.2]));
      const {data} = await axios.post<Plan>(`${API}/plans`, {
        start_lat: start.lat, start_lng: start.lng,
        start_time: new Date().toISOString(), duration_minutes: duration,
        interests: weights, pace, hidden_preference: hidden,
        leg_cap_minutes: legCap, rest_minutes: rest
      });
      onPlan(data);
      navigate('/itinerary');
    } catch (e) {
      if (axios.isAxiosError(e)) setError(typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'Planning request failed. Check the backend and input values.');
      else setError('Could not generate a route.');
    } finally { setLoading(false); }
  }

  return <section className="max-w-3xl mx-auto p-6 space-y-5">
    <h1 className="text-3xl font-bold">Plan your heritage walk</h1>
    <p>Choose your starting point, available time, and interests. Virasat recommends stops automatically.</p>
    <label className="block">Starting point
      <select className="block w-full border rounded p-2" value={startId ?? ''} onChange={e => setStartId(Number(e.target.value))}>
        {sites.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
      </select>
    </label>
    <label className="block">Available time: {duration} minutes
      <input className="block w-full" type="range" min="60" max="480" step="30" value={duration} onChange={e => setDuration(Number(e.target.value))}/>
    </label>
    <label className="block">Walking pace
      <select className="block w-full border rounded p-2" value={pace} onChange={e => setPace(e.target.value)}>
        <option value="normal">Normal</option><option value="gentle">Gentle</option>
      </select>
    </label>
    <label className="block">Maximum walking time between stops: {legCap} minutes
      <input className="block w-full" type="range" min="10" max="120" step="5" value={legCap} onChange={e => setLegCap(Number(e.target.value))}/>
    </label>
    <label className="block">Rest between stops: {rest} minutes
      <input className="block w-full" type="range" min="0" max="30" step="5" value={rest} onChange={e => setRest(Number(e.target.value))}/>
    </label>
    <fieldset><legend className="font-semibold">Interests</legend><div className="flex flex-wrap gap-3">
      {categories.map(c => <label key={c} className="p-2 border rounded"><input type="checkbox" checked={interests.includes(c)} onChange={e => setInterests(old => e.target.checked ? [...old,c] : old.filter(x=>x!==c))}/> {c.replace(/_/g,' ')}</label>)}
    </div></fieldset>
    <label className="block">Hidden heritage preference: {Math.round(hidden*100)}%
      <input className="block w-full" type="range" min="0" max="1" step="0.1" value={hidden} onChange={e=>setHidden(Number(e.target.value))}/>
    </label>
    {error && <p role="alert" className="text-red-700">{error}</p>}
    <button className="bg-indigo-800 text-white px-5 py-3 rounded disabled:opacity-50" disabled={loading || sites.length === 0} onClick={generateRoute}>{loading ? 'Planning…' : 'Generate my walk'}</button>
    <p className="text-sm text-gray-600">Walking times may be estimated. Check local opening hours before visiting.</p>
  </section>;
}

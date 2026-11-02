import React, { useState } from 'react';
import axios from 'axios';
import { Plan, Site } from '../../types';

interface Props {plan: Plan; sites: Site[]; onPlan: (plan: Plan) => void}
export default function ItineraryTimeline({plan,sites,onPlan}: Props) {
  const [minutes,setMinutes]=useState(90);
  const [visited,setVisited]=useState<number[]>([]);
  const [skipped,setSkipped]=useState<number[]>([]);
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const [positionSite,setPositionSite]=useState<number | null>(null);
  const [gps,setGps]=useState<{lat:number;lng:number}|null>(null);
  function useLocation(){
    if (!navigator.geolocation){setError('Location is unavailable in this browser. Select a nearby landmark instead.');return;}
    navigator.geolocation.getCurrentPosition(
      position=>{setGps({lat:position.coords.latitude,lng:position.coords.longitude});setError('');},
      ()=>setError('Location permission was denied or unavailable. Select a nearby landmark instead.'),
      {enableHighAccuracy:true,timeout:10000});
  }
  async function replan() {
    setBusy(true);setError('');
    const first=sites.find(s=>s.id === positionSite) || sites.find(s=>s.id === plan.stops[0]?.site_id);
    if (!gps && !first) {setError('Select a current location first.');setBusy(false);return;}
    const lat=gps?.lat ?? first!.lat;
    const lng=gps?.lng ?? first!.lng;
    try {
      const {data}=await axios.post<Plan>(`${process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'}/plans/replan`,{
        current_lat:lat,current_lng:lng,current_time:new Date().toISOString(),
        new_duration:minutes,visited_ids:visited,skipped_ids:skipped,locked_ids:[],
        previous_stop_ids:plan.stops.map(s=>s.site_id)
      });
      onPlan(data);
    } catch {setError('Could not recalculate this walk.');}
    finally {setBusy(false);}
  }
  return <section className="max-w-3xl mx-auto p-5">
    <h1 className="text-2xl font-bold">Your heritage walk</h1>
    <p>{plan.stops.length} stops · {Math.round(plan.total_duration_minutes)} min total · {Math.round(plan.walking_minutes)} min walking</p>
    <p>Estimated finish: {new Date(plan.finish_time).toLocaleString('en-IN',{timeZone:'Asia/Kolkata'})}</p>
    {plan.engine_notes && <p className="text-sm text-amber-900 bg-amber-50 border border-amber-300 rounded p-3 mt-3">{plan.engine_notes}</p>}
    {!plan.stops.length && <p>No feasible stops for this time window. Try a longer duration or a different starting time.</p>}
    <ol className="space-y-3 mt-4">
      {plan.stops.map((stop,i) => <li key={`${stop.site_id}-${i}`} className="border rounded p-4">
        <strong>{i+1}. {sites.find(s=>s.id===stop.site_id)?.name || `Heritage site ${stop.site_id}`}</strong>
        <p>{Math.round(stop.walking_minutes)} min walking · {stop.visit_minutes} min visiting</p>
        <p className="text-sm">Reason: {stop.reason_codes?.join(', ') || stop.reason}</p>
        {sites.find(s=>s.id===stop.site_id)?.confidence === 'low' && <p className="text-xs text-amber-800">Location data is source-referenced but has not been field-verified.</p>}
        <div className="flex gap-4 mt-2">
          <label><input type="checkbox" checked={visited.includes(stop.site_id)} onChange={e=>setVisited(old=>e.target.checked?[...old,stop.site_id]:old.filter(x=>x!==stop.site_id))}/> Visited</label>
          <label><input type="checkbox" checked={skipped.includes(stop.site_id)} onChange={e=>setSkipped(old=>e.target.checked?[...old,stop.site_id]:old.filter(x=>x!==stop.site_id))}/> Skip</label>
        </div>
      </li>)}
    </ol>
    <div className="border p-4 rounded mt-5"><h2 className="font-semibold">Re-plan mid-walk</h2>
      <p className="text-sm my-2">Choose where you are now or use your device location. This controls the starting point of the new route.</p>
      <label className="block mb-2">Current landmark
        <select className="block w-full border rounded p-2" value={positionSite ?? plan.stops[0]?.site_id ?? ''} onChange={e=>{setPositionSite(Number(e.target.value));setGps(null);}}>
          {sites.map(s=><option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
      </label>
      <button type="button" className="border rounded px-3 py-2 mb-2" onClick={useLocation}>Use my current GPS location</button>
      {gps && <p className="text-sm text-green-700 mb-2">Device location selected ({gps.lat.toFixed(4)}, {gps.lng.toFixed(4)})</p>}
      <label>Remaining time: {minutes} min <input type="range" min="30" max="360" step="15" value={minutes} onChange={e=>setMinutes(Number(e.target.value))}/></label>
      <button className="bg-indigo-800 text-white px-4 py-2 rounded ml-3" disabled={busy} onClick={replan}>{busy?'Replanning…':'Re-plan remaining stops'}</button>
      {error && <p role="alert" className="text-red-700">{error}</p>}
    </div>
    <details className="mt-4"><summary>Why these stops?</summary><pre className="whitespace-pre-wrap text-xs">{JSON.stringify(plan.reasons,null,2)}</pre></details>
  </section>;
}

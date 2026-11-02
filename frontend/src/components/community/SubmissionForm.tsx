import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, getStoredUser } from '../../api';

export default function SubmissionForm() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [category, setCategory] = useState('sultanate');
  const [description, setDescription] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [lat, setLat] = useState('');
  const [lng, setLng] = useState('');
  const [visitMinutes, setVisitMinutes] = useState(30);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  if (!getStoredUser()) return <section className="max-w-xl mx-auto p-6"><h2>Suggest a heritage site</h2><p>Please <Link to="/login">sign in</Link> to submit a site for review.</p></section>;
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setLoading(true); setError('');
    try {
      await api.post('/submissions', {name: name.trim(), category, description: description.trim(), source_url: sourceUrl.trim(), lat: Number(lat), lng: Number(lng), visit_minutes: visitMinutes});
      navigate('/community');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Please check your fields and try again.');
    } finally {setLoading(false);}
  }
  return <section className="max-w-xl mx-auto p-6">
    <h2 className="text-2xl font-semibold mb-2">Suggest a heritage site</h2>
    <p className="text-gray-600 mb-4">Know a lesser-known place in Ahmedabad? Provide its location and a reference. A moderator reviews it before publication.</p>
    <form className="space-y-4" onSubmit={submit}>
      <label className="block">Site name<input className="w-full border rounded p-2" required minLength={3} maxLength={200} value={name} onChange={e=>setName(e.target.value)}/></label>
      <label className="block">Category<select className="w-full border rounded p-2" value={category} onChange={e=>setCategory(e.target.value)}><option value="sultanate">Sultanate / historic monument</option><option value="temples_jain">Temple / Jain heritage</option><option value="pols_living">Pol / living heritage</option><option value="markets_food">Market / food heritage</option><option value="colonial_industrial">Colonial / industrial heritage</option></select></label>
      <label className="block">Historical significance<textarea className="w-full border rounded p-2" required minLength={20} maxLength={3000} rows={4} value={description} onChange={e=>setDescription(e.target.value)} placeholder="What makes this place important?"/></label>
      <label className="block">Reference URL<input className="w-full border rounded p-2" required type="url" value={sourceUrl} onChange={e=>setSourceUrl(e.target.value)} placeholder="https://..."/></label>
      <div className="grid grid-cols-2 gap-3">
        <label>Latitude<input className="w-full border rounded p-2" required type="number" step="any" min="-90" max="90" value={lat} onChange={e=>setLat(e.target.value)}/></label>
        <label>Longitude<input className="w-full border rounded p-2" required type="number" step="any" min="-180" max="180" value={lng} onChange={e=>setLng(e.target.value)}/></label>
      </div>
      <p className="text-xs text-gray-600">Copy coordinates from a map. Submissions are not automatically published.</p>
      <label className="block">Suggested visit (minutes)<input className="w-full border rounded p-2" type="number" min="5" max="240" value={visitMinutes} onChange={e=>setVisitMinutes(Number(e.target.value))}/></label>
      {error && <p role="alert" className="text-red-700">{error}</p>}
      <button className="btn btn-primary w-full" disabled={loading} type="submit">{loading ? 'Sending...' : 'Submit for review'}</button>
    </form>
  </section>;
}

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, getStoredUser } from '../../api';

interface Contribution {id: number; name: string; status: string; moderator_note?: string | null}
export default function CommunityFeed() {
  const user = getStoredUser();
  const [items, setItems] = useState<Contribution[]>([]);
  const [loading, setLoading] = useState(Boolean(user));
  const [error, setError] = useState('');
  useEffect(() => {
    if (!user) return;
    api.get('/submissions/mine').then(r=>setItems(r.data.submissions || []))
      .catch(()=>setError('Unable to load your contributions. Please sign in again.'))
      .finally(()=>setLoading(false));
  }, [user?.id]); // eslint-disable-line react-hooks/exhaustive-deps
  return <section className="max-w-2xl mx-auto p-6">
    <h2 className="text-2xl font-semibold">Community heritage contributions</h2>
    <p className="text-gray-600 my-3">Help discover overlooked places. Suggestions are reviewed before they appear in the planner.</p>
    <Link className="btn btn-primary inline-block my-3" to="/submission">Suggest a site</Link>
    {!user && <p><Link to="/login">Sign in</Link> to view your submissions and review status.</p>}
    {loading && <p>Loading your submissions...</p>}
    {error && <p role="alert" className="text-red-700">{error}</p>}
    {user && !loading && !error && items.length === 0 && <p>No submissions yet. Share a heritage site to get started.</p>}
    <ul className="space-y-3">{items.map(item=><li key={item.id} className="p-4 border rounded bg-white">
      <div className="flex justify-between gap-4"><strong>{item.name}</strong><span className="text-sm">{item.status.replace('_',' ')}</span></div>
      {item.moderator_note && <p className="text-sm mt-2">Moderator feedback: {item.moderator_note}</p>}
    </li>)}</ul>
  </section>;
}

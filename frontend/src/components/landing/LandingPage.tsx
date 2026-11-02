import React, {useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import {api} from '../../api';
import {Site} from '../../types';

export default function LandingPage(){
  const [sites,setSites]=useState<Site[]>([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState('');
  useEffect(()=>{
    api.get<{items:Site[]}>('/sites').then(response=>setSites(response.data.items))
      .catch(()=>setError('Heritage sites are unavailable right now. You can still open the planner and retry.'))
      .finally(()=>setLoading(false));
  },[]);
  return <div className="max-w-6xl mx-auto px-5 py-8">
    <header className="rounded-xl p-8 md:p-14 bg-amber-50 border border-amber-200">
      <p className="uppercase tracking-widest text-sm text-amber-900">Ahmedabad's historic city</p>
      <h1 className="text-4xl md:text-6xl font-bold mt-3 text-red-900">Virasat</h1>
      <p className="text-2xl mt-2 text-gray-800">Heritage, Rediscovered</p>
      <p className="max-w-2xl mt-5 text-gray-700">Explore Ahmedabad at your pace. Choose a time budget and the heritage that interests you. Virasat builds an explainable walk you can adjust along the way.</p>
      <Link to="/planning" className="inline-block mt-6 bg-indigo-900 text-white px-6 py-3 rounded-lg">Plan my heritage walk</Link>
    </header>
    <section className="mt-10" aria-labelledby="explore-title">
      <div className="flex justify-between flex-wrap gap-3 items-center">
        <h2 id="explore-title" className="text-2xl font-semibold">Heritage places to explore</h2>
        <Link to="/community" className="text-indigo-800 underline">Suggest a lesser-known site</Link>
      </div>
      {loading && <p className="mt-4" role="status">Loading heritage locations...</p>}
      {error && <p role="alert" className="mt-4 text-red-800">{error}</p>}
      {!loading && !error && sites.length === 0 && <p className="mt-4">No sites are published yet. Please check back soon.</p>}
      <ul className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-5">
        {sites.slice(0,12).map(site=><li key={site.id} className="rounded-lg border bg-white p-5">
          <h3 className="text-lg font-semibold text-red-900">{site.name}</h3>
          {site.summary && <p className="text-gray-700 mt-2 text-sm">{site.summary}</p>}
          <p className="text-sm mt-3 text-gray-600">Suggested visit: {site.visit_minutes} minutes</p>
          {site.confidence==='low' && <p className="text-xs text-amber-800 mt-2">Location reference not field-verified</p>}
          {!site.hours_verified && <p className="text-xs text-amber-800 mt-1">Confirm opening hours locally</p>}
        </li>)}
      </ul>
      {!loading && sites.length>12 && <p className="mt-4 text-sm text-gray-600">Explore all {sites.length} locations through the planner.</p>}
    </section>
  </div>;
}

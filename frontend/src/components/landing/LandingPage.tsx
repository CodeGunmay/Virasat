import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../api';
import { Site } from '../../types';

const labels: Record<string, string> = {
  sultanate: 'Sultanate heritage',
  temples_jain: 'Temples & Jain',
  pols_living: 'Living heritage',
  markets_food: 'Markets & food',
  colonial_industrial: 'Colonial & industrial'
};

export default function LandingPage() {
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get<{items: Site[]}>('/sites');
      setSites(data.items);
    } catch {
      setError('We could not load the heritage collection. Please try again in a moment.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return <div className="landing-page">
    <section className="hero">
      <div className="hero-copy">
        <span className="eyebrow"><span className="gold-star">✦</span> AHMEDABAD · THE WALLED CITY</span>
        <h1>Your heritage walk, <em>fitted to your time.</em></h1>
        <p>Discover timeless lanes, grand monuments and living traditions. Tell us how long you have; we'll create a thoughtful walking route.</p>
        <div className="hero-actions"><Link to="/planning" className="btn btn-primary">Plan my walk <span aria-hidden="true">↗</span></Link><span className="hero-note">Free to explore · No account needed</span></div>
      </div>
      <div className="hero-art" role="img" aria-label="Illustration of Ahmedabad's historic arches">
        <div className="hero-sun"></div><div className="arch arch-left"></div><div className="arch arch-center"></div><div className="arch arch-right"></div><div className="hero-art-caption"><span>23.0225° N, 72.5714° E</span><strong>Stories around every corner.</strong></div>
      </div>
    </section>

    <section className="how-section section-wrap" aria-labelledby="how-title">
      <div className="section-heading"><div><span className="eyebrow">EFFORTLESS EXPLORATION</span><h2 id="how-title">Three steps to a memorable walk</h2></div><p>Less planning, more discovering.</p></div>
      <div className="steps-grid">
        <article className="step-card"><span className="step-number">01</span><div className="step-icon">◷</div><h3>Tell us your time</h3><p>Choose your hours, interests and walking pace.</p></article>
        <article className="step-card"><span className="step-number">02</span><div className="step-icon">✧</div><h3>We pick what fits and is open</h3><p>Get a route that respects your time and known site hours.</p></article>
        <article className="step-card"><span className="step-number">03</span><div className="step-icon">↝</div><h3>Re-plan anytime</h3><p>Plans change. Your walk can change with them.</p></article>
      </div>
    </section>

    <section className="places-section section-wrap" aria-labelledby="places-title">
      <div className="section-heading"><div><span className="eyebrow">PLACES WITH A STORY</span><h2 id="places-title">A glimpse of old Ahmedabad</h2></div><Link to="/planning" className="text-link">Discover on your walk →</Link></div>
      {loading && <div className="places-grid" role="status" aria-label="Loading heritage sites">{[1,2,3,4,5,6].map(n => <div className="site-skeleton" key={n}><div className="skeleton skeleton-art"></div><div className="skeleton skeleton-line"></div><div className="skeleton skeleton-line short"></div></div>)}</div>}
      {error && <div className="notice error-notice" role="alert"><p>{error}</p><button className="btn btn-outline" onClick={load}>Try again</button></div>}
      {!loading && !error && sites.length === 0 && <div className="notice">No heritage places are listed just yet. Please check back soon.</div>}
      {!loading && !error && <div className="places-grid">{sites.slice(0, 6).map((site, i) => <article className="place-card" key={site.id}>
        <div className={'place-art place-art-' + (i % 3)}><span className="place-art-icon" aria-hidden="true">⌂</span><span className="place-art-count">AHMEDABAD / {String(i+1).padStart(2,'0')}</span></div>
        <div className="place-details"><span className="category-tag">{labels[site.categories?.[0]] || 'Heritage place'}</span><h3>{site.name}</h3><p>{site.summary || 'A fascinating chapter of Ahmedabad’s heritage.'}</p><div className="place-meta"><span>◷ {site.visit_minutes} min visit</span><span className={'hours-badge ' + (site.hours_verified ? 'verified' : 'unverified')}>{site.hours_verified ? '✓ Hours verified' : '◷ Hours unverified'}</span></div></div>
      </article>)}</div>}
      {!loading && !error && sites.length > 6 && <p className="places-footer">Explore all {sites.length} heritage locations through your personal itinerary.</p>}
    </section>
  </div>;
}

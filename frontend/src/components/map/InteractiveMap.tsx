import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Plan, Site } from '../../types';

interface Props {plan?: Plan | null; sites?: Site[]}

export default function InteractiveMap({plan, sites = []}: Props) {
  const element = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<L.Map | null>(null);
  const layers = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!element.current || mapInstance.current) return;
    const map = L.map(element.current, {scrollWheelZoom: false}).setView([23.026, 72.588], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
      maxZoom: 19
    }).addTo(map);
    const group = L.layerGroup().addTo(map);
    mapInstance.current = map;
    layers.current = group;
    const update = () => map.invalidateSize();
    window.addEventListener('resize', update);
    const timer = window.setTimeout(update, 150);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener('resize', update);
      map.remove();
      mapInstance.current = null;
      layers.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapInstance.current;
    const group = layers.current;
    if (!map || !group) return;
    group.clearLayers();
    const points: L.LatLngExpression[] = [];
    plan?.stops.forEach((stop, i) => {
      if (!Number.isFinite(stop.lat) || !Number.isFinite(stop.lng) || (stop.lat === 0 && stop.lng === 0)) return;
      points.push([stop.lat, stop.lng]);
      const pin = L.divIcon({
        className: 'virasat-marker',
        html: '<span>' + (i + 1) + '</span>',
        iconSize: [34, 34],
        iconAnchor: [17, 17]
      });
      const popup = document.createElement('span');
      popup.textContent = (i + 1) + '. ' + (sites.find(s => s.id === stop.site_id)?.name || 'Heritage stop');
      L.marker([stop.lat, stop.lng], {icon: pin}).bindPopup(popup).addTo(group);
    });
    const route = plan?.route_geometry?.filter(p => Number.isFinite(p.lat) && Number.isFinite(p.lng) && (p.lat !== 0 || p.lng !== 0)).map(p => [p.lat, p.lng] as L.LatLngExpression);
    if (route && route.length > 1) L.polyline(route, {color: '#b84f55', weight: 4, opacity: .75, dashArray: '7 9'}).addTo(group);
    if (points.length) map.fitBounds(L.latLngBounds(points), {padding: [40, 40], maxZoom: 16});
    window.setTimeout(() => map.invalidateSize(), 150);
  }, [plan, sites]);

  return <section className="map-card" aria-label="Map of your heritage walk">
    <div className="map-card-head"><div><span className="eyebrow">FOLLOW YOUR JOURNEY</span><h2>Your route, mapped</h2></div><span className="map-live">● Heritage map</span></div>
    <div ref={element} className="map-canvas" role="application" aria-label="Map with numbered heritage stops" />
    <div className="map-card-foot"><span>⌖ Ahmedabad, India</span><span>Numbered pins match the stops</span></div>
    <p className="map-note">Illustrative route only — lines are not verified walking directions.</p>
  </section>;
}

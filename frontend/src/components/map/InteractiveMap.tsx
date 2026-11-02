import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Plan, Site } from '../../types';

interface Props { plan?: Plan | null; sites?: Site[] }
export default function InteractiveMap({plan, sites = []}: Props) {
  const element = useRef<HTMLDivElement>(null);
  const mapInstance = useRef<L.Map | null>(null);
  const layers = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!element.current || mapInstance.current) return;
    const map = L.map(element.current).setView([23.0260,72.5880], 14);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>', maxZoom: 19
    }).addTo(map);
    const group = L.layerGroup().addTo(map);
    mapInstance.current = map; layers.current = group;
    return () => {map.remove(); mapInstance.current = null; layers.current = null;};
  }, []);

  useEffect(() => {
    const map = mapInstance.current;
    const group = layers.current;
    if (!map || !group) return;
    group.clearLayers();
    const selected = plan ? plan.stops.map(stop => ({...stop, name: sites.find(s => s.id === stop.site_id)?.name || `Site ${stop.site_id}`})) : [];
    const points: L.LatLngExpression[] = [];
    selected.forEach((stop, i) => {
      if (!Number.isFinite(stop.lat) || !Number.isFinite(stop.lng) || (stop.lat === 0 && stop.lng === 0)) return;
      points.push([stop.lat,stop.lng]);
      const popupText = document.createElement('span');
      popupText.textContent = `${i+1}. ${stop.name}`;
      L.circleMarker([stop.lat,stop.lng], {radius: 9, color:'#8b3349', fillOpacity: 0.85}).bindPopup(popupText).addTo(group);
    });
    if (plan?.route_geometry?.length) {
      const route = plan.route_geometry.filter(p => Number.isFinite(p.lat) && Number.isFinite(p.lng) && (p.lat !== 0 || p.lng !== 0)).map(p => [p.lat,p.lng] as L.LatLngExpression);
      if (route.length > 1) L.polyline(route, {color:'#303f80', weight:4}).addTo(group);
    }
    if (points.length) map.fitBounds(L.latLngBounds(points), {padding:[35,35]});
  }, [plan, sites]);

  return <section className="p-4"><h2 className="text-xl font-semibold mb-2">Heritage map</h2><div ref={element} style={{height:420,width:'100%'}} role="application" aria-label="Map of heritage stops"/><p className="text-sm text-gray-600">Lines may be approximate; use a navigation service for walking directions.</p></section>;
}

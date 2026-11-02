"""Explainable greedy walk planner with conservative data handling.

Distances are estimates, not pedestrian-network routing. Unknown opening hours are
allowed only as explicitly unverified visits; the API never calls them confirmed open.
"""
from datetime import datetime, timedelta
from math import atan2, cos, radians, sin, sqrt
from zoneinfo import ZoneInfo

from db.models import Site, SiteRestriction, SiteSchedule

IST = ZoneInfo("Asia/Kolkata")
CITY_CENTER = (23.0260, 72.5880)


def distance_m(lat1, lon1, lat2, lon2):
    r1, r2 = radians(lat1), radians(lat2)
    dr, dl = r2 - r1, radians(lon2 - lon1)
    a = sin(dr / 2) ** 2 + cos(r1) * cos(r2) * sin(dl / 2) ** 2
    return 6371000 * 2 * atan2(sqrt(a), sqrt(max(0, 1-a)))


def estimate_walk_minutes(a, b, pace):
    speed = 50 if pace == "gentle" else 80
    return round(distance_m(*a, *b) * 3.5 / speed, 1)


def hours_state(db, site_id, arrival, departure):
    """Return (allowed, verified) without inventing schedules.

    Unknown hours remain eligible but explicitly unverified. A known day's hours
    must contain the entire visit; known restrictions override those windows.
    """
    rows = db.query(SiteSchedule).filter(SiteSchedule.site_id == site_id).all()
    if not rows:
        return True, False
    if arrival.date() != departure.date():
        return False, True
    weekday = arrival.strftime('%A').lower()
    slots = [r for r in rows if str(r.weekday).lower() == weekday and r.open and r.close]
    if not any(r.open <= arrival.strftime('%H:%M') and departure.strftime('%H:%M') <= r.close for r in slots):
        return False, True
    restrictions = db.query(SiteRestriction).filter(SiteRestriction.site_id == site_id).all()
    for r in restrictions:
        day_or_date = (r.weekday_or_date or '').strip().lower()
        if day_or_date and day_or_date not in (weekday, arrival.date().isoformat()):
            continue
        start = getattr(r, 'start', None)
        end = getattr(r, 'end', None)
        if start and end and str(start) < departure.strftime('%H:%M') and str(end) > arrival.strftime('%H:%M'):
            return False, True
    return True, True


def make_plan(db, *, start_lat, start_lng, start_time, duration_minutes, interests,
              pace='normal', hidden_preference=0.5, visited=(), skipped=(), locked=(),
              leg_cap_minutes=None, rest_minutes=0):
    now = start_time.astimezone(IST) if start_time.tzinfo else start_time.replace(tzinfo=IST)
    budget = float(duration_minutes)
    if budget <= 0:
        raise ValueError('Time budget must be positive')
    rest_minutes = max(0, int(rest_minutes or 0))
    candidates = db.query(Site).filter(Site.status == 'approved').all()
    # Initial release only covers the historic core, not distant city attractions.
    candidates = [s for s in candidates if distance_m(s.lat, s.lng, *CITY_CENTER) <= 2500]
    excluded = []
    remaining = {s.id:s for s in candidates if s.id not in set(visited) | set(skipped)}
    for s in candidates:
        if s.id in skipped: excluded.append({'site_id':s.id,'reason':'user_skipped'})
        elif s.id in visited: excluded.append({'site_id':s.id,'reason':'already_visited'})
    stops = []
    position = (float(start_lat),float(start_lng))
    elapsed = 0.0
    walking = 0.0
    visiting = 0.0
    while remaining:
        options = []
        for s in remaining.values():
            travel = estimate_walk_minutes(position,(s.lat,s.lng),pace)
            if leg_cap_minutes is not None and travel > leg_cap_minutes:
                continue
            visit = max(int(s.visit_minutes),1)
            rest = rest_minutes if stops else 0
            start_visit = now + timedelta(minutes=elapsed + travel + rest)
            end_visit = start_visit + timedelta(minutes=visit)
            allowed, verified = hours_state(db,s.id,start_visit,end_visit)
            if not allowed or elapsed+travel+rest+visit > budget:
                continue
            categories = s.categories or []
            relevance = sum(float(interests.get(c,0)) for c in categories)
            value = 1 + relevance + (2*hidden_preference if s.hidden_tier else 0)
            if s.id in locked: value += 100
            score = value / max(1,travel+rest+visit)
            options.append((-score,s.id,s,travel,visit,verified,relevance,rest))
        if not options: break
        _, _, site, travel, visit, verified, relevance, rest = min(options)
        elapsed += travel+rest+visit
        walking += travel
        visiting += visit
        reason = 'locked' if site.id in locked else ('interest_match' if relevance else 'nearby_fit')
        stops.append({'site_id':site.id,'lat':site.lat,'lng':site.lng,
                      'walking_minutes':round(travel,1),'visit_minutes':visit,
                      'reason':reason,'reason_codes':[reason] + ([] if verified else ['hours_unverified'])})
        position=(site.lat,site.lng)
        remaining.pop(site.id)
    for s in remaining.values():
        travel = estimate_walk_minutes(position,(s.lat,s.lng),pace)
        arrival=now+timedelta(minutes=elapsed+travel)
        allowed,_=hours_state(db,s.id,arrival,arrival+timedelta(minutes=s.visit_minutes))
        why='closed_at_arrival' if not allowed else ('over_leg_cap' if leg_cap_minutes is not None and travel > leg_cap_minutes else 'over_budget')
        excluded.append({'site_id':s.id,'reason':why})
    geometry=[{'lat':s['lat'],'lng':s['lng']} for s in stops]
    note='Walking times are distance-based estimates (3.5× detour factor); they are not verified pedestrian routes.'
    if any('hours_unverified' in s['reason_codes'] for s in stops):
        note += ' Some site opening hours are unverified; confirm locally before visiting.'
    if any(site_id not in [s['site_id'] for s in stops] for site_id in locked):
        note += ' One or more locked stops could not fit the current constraints.'
    if rest_minutes:
        note += f' Includes {rest_minutes}-minute breaks between stops.'
    return {'stops':stops,'total_minutes':round(elapsed,1),'walking_minutes':round(walking,1),
            'visiting_minutes':round(visiting,1),'finish_time':now+timedelta(minutes=elapsed),
            'predicted_completion':now+timedelta(minutes=budget),
            'geometry':geometry,'reasons':[{'site_id':s['site_id'],'codes':s['reason_codes'],'included':True} for s in stops]+excluded,
            'engine_notes':note}

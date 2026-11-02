"""Isolated API acceptance tests. Never modify bundled sample data."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from main import app
from db.base import get_db
from db.models import Base, City, Site, SiteSchedule, SiteRestriction, User, Submission, SiteSource

@pytest.fixture()
def client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    with Session() as db:
        db.add(City(id=1,name='Test City',timezone='Asia/Kolkata'))
        db.add_all([
            Site(id=1,city_id=1,name='Site A',lat=23.0225,lng=72.5751,categories=['sultanate'],visit_minutes=30,status='approved',confidence='high'),
            Site(id=2,city_id=1,name='Site B',lat=23.023,lng=72.5755,categories=['pols_living'],visit_minutes=40,status='approved',confidence='high'),
            Site(id=3,city_id=1,name='Closed Site',lat=23.021,lng=72.575,categories=['sultanate'],visit_minutes=30,status='approved',confidence='high'),
        ])
        db.add(SiteSchedule(site_id=3,weekday='Monday',open='07:00',close='08:00'))
        db.commit()
    def override():
        with Session() as db:
            yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()

def payload(duration=100):
    return {'start_lat':23.0225,'start_lng':72.5751,'start_time':'2026-11-02T10:00:00+05:30',
            'duration_minutes':duration,'interests':{'sultanate':2,'pols_living':1}}

def test_health_and_schema(client):
    assert client.get('/health').status_code == 200
    assert '/plans' in client.get('/openapi.json').json()['paths']

def test_plan_time_budget_and_closed_site(client):
    response=client.post('/plans',json=payload())
    assert response.status_code == 200, response.text
    body=response.json()
    assert body['total_duration_minutes'] <= 100
    assert 3 not in [s['site_id'] for s in body['stops']]
    assert all('lat' in s for s in body['stops'])

def test_replan_respects_visited_skipped(client):
    response=client.post('/plans/replan',json={
        'current_lat':23.0225,'current_lng':72.5751,'current_time':'2026-11-02T10:00:00+05:30',
        'new_duration':90,'visited_ids':[1],'skipped_ids':[3],'locked_ids':[2],
        'previous_stop_ids':[1,2], 'interests':{'pols_living':2}})
    assert response.status_code == 200, response.text
    body=response.json()
    ids=[s['site_id'] for s in body['stops']]
    assert 1 not in ids and 3 not in ids and 2 in ids
    assert body['diff']['removed'] == []

def test_invalid_budget_and_protected_me(client):
    assert client.post('/plans',json=payload(0)).status_code == 422
    assert client.get('/auth/me').status_code == 401

def test_site_filters_and_unverified_hours(client):
    only_pols=client.get('/sites?category=pols_living').json()
    assert [site['id'] for site in only_pols['items']]==[2]
    assert only_pols['total']==1
    assert client.get('/sites?category=unknown').json()['total']==0
    assert client.get('/sites?open_now=true').json()['total'] == 0

def test_leg_cap_and_breaks_are_enforced(client):
    req=payload(180)
    req['leg_cap_minutes']=1
    constrained=client.post('/plans',json=req)
    assert constrained.status_code==200
    assert all(s['walking_minutes']<=1 for s in constrained.json()['stops'])
    req.pop('leg_cap_minutes')
    req['rest_minutes']=25
    with_breaks=client.post('/plans',json=req)
    assert with_breaks.status_code==200
    body=with_breaks.json()
    assert body['total_duration_minutes'] <= 180
    if len(body['stops'])>1:
        assert body['total_duration_minutes'] >= body['walking_minutes']+body['visiting_minutes']+25*(len(body['stops'])-1)-0.2

def test_registration_login_and_role_boundary(client):
    register=client.post('/auth/register',json={'email':'gunmay@example.com','password':'test-password-123','role':'moderator'})
    assert register.status_code == 201, register.text
    assert register.json()['user']['role'] == 'visitor'
    assert client.post('/auth/register',json={'email':'gunmay@example.com','password':'test-password-123'}).status_code == 409
    assert client.post('/auth/login',json={'email':'gunmay@example.com','password':'wrong-password'}).status_code == 401
    login=client.post('/auth/login',json={'email':'gunmay@example.com','password':'test-password-123'})
    assert login.status_code == 200, login.text
    headers={'Authorization':f"Bearer {login.json()['access_token']}"}
    assert client.get('/auth/me',headers=headers).json()['email']=='gunmay@example.com'
    assert client.get('/moderation/queue',headers=headers).status_code == 403
    proposal={'name':'A newly found historic lane','category':'pols_living',
              'description':'A documented historic lane requiring independent verification.',
              'source_url':'https://example.org/heritage-reference','lat':23.023,'lng':72.577,'visit_minutes':20}
    submitted=client.post('/submissions',json=proposal,headers=headers)
    assert submitted.status_code == 201, submitted.text
    assert submitted.json()['status']=='pending'
    own=client.get('/submissions/mine',headers=headers)
    assert own.status_code == 200 and len(own.json()['submissions'])==1
    assert client.post('/moderation/1/decision',headers=headers,json={'decision':'approve','moderator_note':'Reviewed sources'}).status_code == 403

def test_restriction_blocks_overlapping_visit(client):
    from engine.safe_planner import hours_state, IST
    from datetime import datetime
    with next(app.dependency_overrides[get_db]()) as db:
        db.add(SiteSchedule(site_id=1,weekday='Monday',open='09:00',close='17:00'))
        db.add(SiteRestriction(site_id=1,weekday_or_date='Monday',start='10:00',end='11:00',reason='Restricted access'))
        db.commit()
        arrival=datetime(2026,11,2,10,15,tzinfo=IST)
        departure=datetime(2026,11,2,10,45,tzinfo=IST)
        assert hours_state(db,1,arrival,departure)==(False,True)

def test_100_dynamic_budget_scenarios(client):
    """Reproducible 100-case invariants test, not a quality/optimality benchmark."""
    for minutes in range(20,220,2):
        body=payload(minutes)
        body['start_lat']=23.0225 + ((minutes % 7) - 3) * 0.0001
        body['interests']={'sultanate':minutes % 4, 'pols_living':(minutes // 3) % 3}
        first=client.post('/plans',json=body)
        second=client.post('/plans',json=body)
        assert first.status_code==second.status_code==200
        result=first.json()
        assert result['total_duration_minutes'] <= minutes
        assert len({stop['site_id'] for stop in result['stops']})==len(result['stops'])
        assert 3 not in [stop['site_id'] for stop in result['stops']]
        assert result==second.json()

def test_moderation_approval_creates_sourced_site(client):
    from core.security import hash_password
    with next(app.dependency_overrides[get_db]()) as db:
        db.add(User(email='reviewer@example.com', password_hash=hash_password('reviewer-password-123'),role='moderator'))
        db.commit()
    login=client.post('/auth/login',json={'email':'reviewer@example.com','password':'reviewer-password-123'})
    assert login.status_code==200
    headers={'Authorization':f"Bearer {login.json()['access_token']}"}
    with next(app.dependency_overrides[get_db]()) as db:
        moderator=db.query(User).filter(User.email=='reviewer@example.com').one()
        db.add(Submission(user_id=moderator.id,status='pending',proposed_data={
            'name':'Documented heritage spot','category':'historical',
            'description':'A well-documented heritage location for human review.',
            'source_url':'https://example.org/reviewed-source',
            'lat':23.0225,'lng':72.5751,'visit_minutes':25}))
        db.commit()
    queue=client.get('/moderation/queue',headers=headers)
    assert queue.status_code==200
    submission_id=queue.json()['submissions'][0]['id']
    decision=client.post(f'/moderation/{submission_id}/decision',headers=headers,
        json={'decision':'approve','moderator_note':'Source and coordinates checked'})
    assert decision.status_code==200,decision.text
    site_id=decision.json()['site_id']
    detail=client.get(f'/sites/{site_id}')
    assert detail.status_code==200
    assert detail.json()['sources'][0]['url']=='https://example.org/reviewed-source'
    assert client.post(f'/moderation/{submission_id}/decision',headers=headers,
        json={'decision':'approve','moderator_note':'Duplicate decision'}).status_code==409


def test_csv_schedule_import_excludes_closed_site(client, tmp_path):
    from db.seed_heritage import load_schedules
    csv_file = tmp_path / 'hours.csv'
    csv_file.write_text(
        'site_name,weekday,open_time,close_time,source_url\n'
        'Site A,0,07:00,08:00,https://example.org/opening-hours\n',
        encoding='utf-8'
    )
    with next(app.dependency_overrides[get_db]()) as db:
        assert load_schedules(db, csv_file) == 1
        db.commit()
        assert load_schedules(db, csv_file) == 0
        assert db.query(SiteSchedule).filter(SiteSchedule.site_id == 1).count() == 1
        db.commit()

    response = client.post('/plans', json=payload())
    assert response.status_code == 200
    assert 1 not in [stop['site_id'] for stop in response.json()['stops']]
    assert client.get('/sites/1').json()['schedules'][0]['weekday'] == 'monday'

    csv_file.write_text(
        'site_name,weekday,open_time,close_time,source_url\n'
        'Missing Site,0,07:00,08:00,https://example.org/opening-hours\n',
        encoding='utf-8'
    )
    with next(app.dependency_overrides[get_db]()) as db:
        with pytest.raises(ValueError, match='unknown site name'):
            load_schedules(db, csv_file)

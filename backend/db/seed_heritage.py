"""Idempotent, source-labelled Ahmedabad historic-core starter dataset.

Coordinates are sourced from a Wikimedia monument coordinate list, not field
verified. Visiting durations are planning estimates; opening hours are UNKNOWN.
No invented access windows or claims of confirmed public entry are added.
"""
from datetime import datetime, timezone
from db.base import engine, SessionLocal
from db.models import Base, City, Site, SiteSource

COORD_SOURCE = 'https://en.wikipedia.org/wiki/List_of_Monuments_of_National_Importance_in_Ahmedabad_district'
HERITAGE_SOURCE = 'https://whc.unesco.org/en/list/1551'
DETAIL_SOURCES = {
    'Kavi Dalpatram Chowk': ('https://commons.wikimedia.org/wiki/File:Poet_Dalpatram_Chowk.jpg',
                             'https://heritage.ahmedabadcity.gov.in/details/115/heritage_site/morning-walk/en'),
    'Manek Chowk': ('https://en.wikipedia.org/wiki/Manek_Chowk_(Ahmedabad)',
                    'https://heritage.ahmedabadcity.gov.in/morning-walk/'),
    'Swaminarayan Temple Kalupur': ('https://www.wikidata.org/wiki/Q12060943',
                                    'https://heritage.ahmedabadcity.gov.in/details/113/heritage_site/morning-walk/en'),
}

# Name, latitude, longitude, category, planning visit minutes, publicly checkable context.
RECORDS = [
    ('Azam Khan Sarai gates', 23.023855,72.581440,'sultanate',15,'Historic gateways near Bhadrakali Temple in Ahmedabad.'),
    ('Bhadra Gate',23.024260,72.581501,'sultanate',20,'Gate within Ahmedabad’s Sultanate-era Bhadra precinct.'),
    ('Sidi Saiyyed Mosque',23.027080,72.581030,'sultanate',25,'Historic mosque known for its stone latticework; respect active worship.'),
    ('Ahmed Shah Mosque',23.022701,72.578980,'sultanate',20,'Early mosque in the historic Bhadra area; check visitor access.'),
    ('Teen Darwaza',23.024336,72.584545,'sultanate',15,'Three-arched historic gateway in the old-city market precinct.'),
    ('Shah Khoob Mosque',23.023815,72.583200,'sultanate',15,'Protected historic mosque near the central city gateways.'),
    ('Jama Masjid',23.023870,72.587090,'sultanate',30,'Major historic congregational mosque and AMC heritage-walk endpoint.'),
    ('Rani no Hajiro',23.023742,72.589119,'sultanate',20,'Royal tomb precinct beside the old-city market quarter.'),
    ('Badshah no Hajiro',23.023792,72.587954,'sultanate',20,'Mausoleum of Ahmedabad’s founding ruler near Jama Masjid.'),
    ('Panchkuva Gate',23.025120,72.597240,'sultanate',15,'Historic gate at the eastern side of the old city.'),
    ('Queen’s Mosque Sarangpur',23.022858,72.595890,'sultanate',20,'Historic mosque in the Sarangpur district; check visitor access.'),
    ('Sarangpur Queen’s Tomb',23.022883,72.596235,'sultanate',15,'Protected tomb close to Sarangpur Queen’s Mosque.'),
    ('Sidi Bashir Mosque',23.023710,72.599750,'sultanate',25,'Historic mosque associated with the Jhulta Minar monument.'),
    ('Delhi Gate',23.037851,72.587983,'sultanate',15,'North-side gate of Ahmedabad’s historic city.'),
    ('Qutub Shah Mosque',23.0353252,72.5873828,'sultanate',20,'Protected mosque in the northern historic-city area.'),
    ('Kalupur Gate',23.030840,72.597990,'sultanate',15,'Historic gateway near Kalupur.'),
    ('Sarangpur Gate',23.022500,72.598056,'sultanate',15,'One of Ahmedabad’s old fortified city gates.'),
    ('Dariyapur Gate',23.037440,72.592950,'sultanate',15,'Historic gateway serving the Dariyapur quarter.'),
    ('Prem Darwaza',23.035000,72.596667,'sultanate',15,'Historic gate in Ahmedabad’s northern old-city area.'),
    ('Muhafiz Khan Mosque',23.033130,72.588060,'sultanate',20,'Protected historic mosque; visitor access requires checking.'),
    ('Rani Rupamati Mosque',23.031792,72.583744,'sultanate',25,'Sultanate-era mosque distinguished by its architectural heritage.'),
    ('Shahpur Kazi Chisti Mosque',23.0376798,72.5804191,'sultanate',20,'Protected historic mosque in the Shahpur area.'),
    ('Dastur Khan Mosque',23.0177778,72.5891667,'sultanate',20,'Protected historic mosque in the southern core.'),
    ('Rani Sipri Mosque and Tomb',23.017222,72.590278,'sultanate',25,'Mosque and associated tomb in Ahmedabad’s historic city.'),
    ('Astodiya Gate',23.016815,72.590928,'sultanate',15,'Historic gate at Astodiya.'),
    ('Raipur Gate',23.017222,72.594722,'sultanate',15,'Historic gateway at Raipur.'),
    ('Kavi Dalpatram Chowk',23.029222,72.591678,'pols_living',30,'Public square honouring Gujarati poet and social reformer Dalpatram.'),
    ('Manek Chowk',23.023611,72.588611,'markets_food',30,'Historic city square with daytime markets and evening food activity.'),
    ('Swaminarayan Temple Kalupur',23.030000,72.591000,'temples_jain',30,'Historic Swaminarayan temple complex in Kalupur; respect worship and visitor rules.'),
]

def seed():
    Base.metadata.create_all(bind=engine)
    inserted=0
    with SessionLocal() as db:
        city=db.query(City).filter(City.name=='Ahmedabad').one_or_none()
        if city is None:
            city=City(name='Ahmedabad',timezone='Asia/Kolkata')
            db.add(city)
            db.flush()
        existing={s.name.casefold() for s in db.query(Site).filter(Site.city_id==city.id).all()}
        for name,lat,lng,category,visit,summary in RECORDS:
            if name.casefold() in existing:
                continue
            site=Site(city_id=city.id,name=name,lat=lat,lng=lng,
                      categories=[category],visit_minutes=visit,summary=summary,
                      status='approved',confidence='low',hidden_tier=False)
            db.add(site)
            db.flush()
            coord_source, history_source = DETAIL_SOURCES.get(name,(COORD_SOURCE,HERITAGE_SOURCE))
            db.add_all([
                SiteSource(site_id=site.id,url=coord_source,title='Coordinate reference (not field verified)'),
                SiteSource(site_id=site.id,url=history_source,title='Heritage context')
            ])
            inserted+=1
        db.commit()
    return inserted

if __name__=='__main__':
    print(f'New heritage sites seeded: {seed()} (coordinates and hours still require field verification)')

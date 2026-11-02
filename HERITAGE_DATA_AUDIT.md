# Ahmedabad heritage data — provenance and release gate

Virasat's bundled database is **sample data**, not a verified production gazetteer. Do not call its location coordinates, site hours, or historical summaries verified until each record has been checked and reviewed.

The current idempotent seeder (`backend/db/seed_heritage.py`) contains 29 heritage candidates. Twenty-six use a Wikimedia coordinate list of protected Ahmedabad monuments. Three use their own public map references (Wikimedia Commons, Wikipedia and Wikidata) with corresponding AMC heritage pages where available. Every imported site is marked low confidence; all visit durations are estimates; no operating-hours rows are created. The previous Arena SQLite database is not a source of verified facts and is excluded from shareable ZIP releases.

## Reliable starting references (accessed 2 November 2026)

- Ahmedabad Municipal Corporation, heritage walk: https://heritage.ahmedabadcity.gov.in/morning-walk/
- AMC, all heritage places: https://heritage.ahmedabadcity.gov.in/all_heritages/
- AMC, Teen Darwaza (describes all-hours public access and an approximate ten-minute visit): https://heritage.ahmedabadcity.gov.in/details/71/heritage_site/en
- AMC, Kavi Dalpatram Chowk (describes any-time access and an approximate thirty-minute visit): https://heritage.ahmedabadcity.gov.in/details/115/heritage_site/morning-walk/en
- UNESCO, Historic City of Ahmadabad: https://whc.unesco.org/en/list/1551
- Gujarat Tourism, official heritage walk overview: https://gujarattourism.com/central-zone/ahmedabad/heritage-walk.html

The official AMC walk connects Kalupur Swaminarayan Temple, neighbourhood pols, Manek Chowk and Jama Masjid. This confirms the *selection of sites*, not exact GPS coordinates or independently navigable pedestrian directions.

## Publication checklist for each site

1. Confirm the name and short original-language summary from an official heritage source.
2. Verify coordinates against a map independently, with at least one on-site or local cross-check if possible; record uncertainty.
3. Record publicly accessible visitor areas only. Do not assume a religious site is open for tourism during worship.
4. Check opening windows, closed days, fees and access restrictions with a current official source. If unknown, leave schedules empty and expose `hours_unverified`.
5. Store source URLs in `site_source` and review dates in `last_verified_on`.
6. Include cultural etiquette and avoid misleading claims that walking estimates are pedestrian navigation.
7. Review the live route map on a phone before using it in a judge demonstration.

**Do not import invented or approximate locations as high-confidence live data.** Routes use straight-line estimates with a 3.5× detour multiplier; geometry is not a sidewalk/path routing service.

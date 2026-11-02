"""Translation routes for Virasat.

Provides interface string translations for multiple languages.
"""

from fastapi import APIRouter, Query
from typing import Dict, Any

router = APIRouter(tags=["translations"])


@router.get("", response_model=Dict[str, Any])
async def get_translation(
    language: str = Query("en", description="Language code (en or hi)"),
) -> dict:
    """Get interface strings in the requested language.

    Initially supports English and Hindi.
    Falls back to English for untranslated strings.
    """
    # English strings
    en_strings = {
        "app_title": "Virasat — Heritage, Rediscovered",
        "plan": "Plan Walk",
        "explore": "Explore",
        "my_walks": "My Walks",
        "saved_routes": "Saved Routes",
        "discover": "Discover",
        "site_detail": "Site Detail",
        "about": "About",
        "logout": "Log Out",
        "login": "Log In",
        "register": "Register",
        "submit_site": "Submit Site",
        "moderation": "Moderation",
        "save_route": "Save Route",
        "share_route": "Share Route",
        "replan": "Re-Plan",
        "gentle_pace": "Gentle Pace",
        "hidden_sites": "Hidden Sites",
        "famous_sites": "Famous Sites",
        "walking_time": "Walking Time",
        "visit_duration": "Visit Duration",
        "opening_hours": "Opening Hours",
        "close": "Close",
        "open": "Open",
        "unknown": "Unknown",
        "error": "Error",
        "success": "Success",
        "loading": "Loading",
        "no_results": "No results found",
        "filter_by_category": "Filter by category",
        "filter_by_tier": "Filter by tier",
        "open_now": "Open now",
        "search_places": "Search places",
        "must_include": "Must include",
        "locked": "Locked",
        "skipped": "Skipped",
        "walk": "Walk",
        "start": "Start",
        "finish": "Finish",
        "minutes": "minutes",
        "today": "Today",
        "yesterday": "Yesterday",
        "monday": "Monday",
        "tuesday": "Tuesday",
        "wednesday": "Wednesday",
        "thursday": "Thursday",
        "friday": "Friday",
        "saturday": "Saturday",
        "sunday": "Sunday",
    }

    # Hindi strings (basic translations)
    hi_strings = {
        "app_title": "विरासत — विरासत दोबारा खोजें",
        "plan": "चलने की योजना बनाएं",
        "explore": "खोजें",
        "my_walks": "मेरा चलना",
        "saved_routes": "सेव किए गए रूट",
        "discover": "खोजें",
        "site_detail": "स्थल विवरण",
        "about": "के बारे में",
        "logout": "बाहर निकलें",
        "login": "लॉगिन",
        "register": "पंजीकरण करें",
        "submit_site": "स्थल प्रस्तुत करें",
        "moderation": "मॉडरेशन",
        "save_route": "मार्ग बचाएं",
        "share_route": "मार्ग साझा करें",
        "replan": "फिर से योजना बनाएं",
        "gentle_pace": "धीमी गति",
        "hidden_sites": "गुमनाम स्थल",
        "famous_sites": "प्रसिद्ध स्थल",
        "walking_time": "चलने का समय",
        "visit_duration": "भेंट अवधि",
        "opening_hours": "खुलने का समय",
        "close": "बंद",
        "open": "खुला",
        "unknown": "अज्ञात",
        "error": "त्रुटि",
        "success": "सफलता",
        "loading": "लोड हो रहा है",
        "no_results": "नहीं मिला",
        "filter_by_category": "श्रेणी द्वारा फ़िल्टर",
        "filter_by_tier": "टियर द्वारा फ़िल्टर",
        "open_now": "अभी खुला है",
        "search_places": "स्थल खोजें",
        "must_include": "ज़रूरी शामिल करें",
        "locked": "बंदlocked",
        "skipped": "छोड़ा गया",
        "walk": "चलना",
        "start": "शुरुआत",
        "finish": "समाप्ति",
        "minutes": "मिनट",
        "today": "आज",
        "yesterday": "कल",
        "monday": "सोमवार",
        "tuesday": "मंगलवार",
        "wednesday": "बुधवार",
        "thursday": "गुरुवार",
        "friday": "शुक्रवार",
        "saturday": "शनिवार",
        "sunday": "रविवार",
    }

    # Return the appropriate language
    if language.startswith("hi"):
        return hi_strings
    else:
        return en_strings
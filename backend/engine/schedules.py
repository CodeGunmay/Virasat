"""Site opening schedule system for Virasat.

Handles weekly opening hours, split slots, closed days,
prayer-time restrictions, and festival closures for heritage sites.

All times are in Asia/Kolkata timezone.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple

import pytz

tz = pytz.timezone("Asia/Kolkata")


# ─── Schedule representation ────────────────────────────────────────────────

class ScheduleWindow:
    """A single open/close window for a day."""

    def __init__(self, open_time: time, close_time: time):
        self.open = open_time
        self.close = close_time

    def is_open_at(self, check_time: datetime) -> bool:
        """Check if the window is open at the given datetime (in Asia/Kolkata TZ)."""
        check_str = check_time.strftime("%H:%M")
        return self.open <= check_str <= self.close

    def minutes_open(self, check_time: datetime) -> int:
        """Minutes remaining in this window from check_time, or 0 if closed."""
        check_str = check_time.strftime("%H:%M")
        if not self.is_open_at(check_time):
            return 0
        # Minutes from check_time to close
        check_minutes = check_time.hour * 60 + check_time.minute
        close_minutes = self.close.hour * 60 + self.close.minute
        return max(close_minutes - check_minutes, 0)


class MultiSlotSchedule:
    """A schedule with multiple open/close slots per day.

    e.g. a site open 09:00-12:00 and 14:00-18:00
    """

    def __init__(self, slots: List[ScheduleWindow]):
        self.slots = slots

    def is_open_at(self, check_time: datetime) -> bool:
        """Check if any slot is open at the given time."""
        for slot in self.slots:
            if slot.is_open_at(check_time):
                return True
        return False

    def minutes_until_close(self, check_time: datetime) -> Optional[int]:
        """Minutes until the current slot closes, or None if currently closed."""
        for slot in self.slots:
            if slot.is_open_at(check_time):
                return slot.minutes_until_close(check_time)
        return None

    def remaining_minutes(self, check_time: datetime) -> int:
        """Minutes remaining in the current or next slot."""
        # Find the first slot that hasn't closed yet
        for slot in self.slots:
            if slot.is_open_at(check_time):
                return slot.minutes_until_close(check_time)
            # Check if check_time is before this slot starts
            check_str = check_time.strftime("%H:%M")
            if slot.open > check_str:
                # Slot starts later today; minutes until it opens
                open_minutes = (slot.open.hour * 60 + slot.open.minute) - (
                    check_time.hour * 60 + check_time.minute
                )
                return max(open_minutes, 0)
        # No slot open; return 0
        return 0


# ─── Schedule loading from database ─────────────────────────────────────────

def load_site_schedule(db, site_id: int) -> MultiSlotSchedule:
    """Load a site's opening schedule from the database.

    Reads site_schedule table rows for the given site and constructs
    a MultiSlotSchedule with all defined windows.
    """
    from ..db.models import SiteSchedule as SiteScheduleModel

    stmt = select(SiteScheduleModel).where(SiteScheduleModel.site_id == site_id)
    result = db.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        # No schedule defined; return a schedule that's always closed
        return MultiSlotSchedule([])

    slots = []
    for row in rows:
        # Parse open/close times; they may be time objects or strings
        open_time = row.open if isinstance(row.open, time) else time.fromisoformat(str(row.open))
        close_time = row.close if isinstance(row.close, time) else time.fromisoformat(str(row.close))
        slots.append(ScheduleWindow(open_time, close_time))

    return MultiSlotSchedule(slots)


# ─── Core schedule checking functions ───────────────────────────────────────

def is_site_open_at(db, site_id: int, check_time: datetime) -> bool:
    """Check whether a site is open at the given datetime (Asia/Kolkata TZ)."""
    schedule = load_site_schedule(db, site_id)
    return schedule.is_open_at(check_time)


def minutes_until_site_closes(db, site_id: int, check_time: datetime) -> Optional[int]:
    """Minutes remaining until a site closes from the given time.

    Returns None if the site is currently closed.
    """
    schedule = load_site_schedule(db, site_id)
    return schedule.minutes_until_close(check_time)


def site_remaining_minutes(db, site_id: int, check_time: datetime) -> int:
    """Minutes remaining in the current/open slot from check_time."""
    schedule = load_site_schedule(db, site_id)
    return schedule.remaining_minutes(check_time)


def check_visit_feasibility(
    db,
    site_id: int,
    arrival_time: datetime,
    visit_minutes: int,
) -> Tuple[bool, dict]:
    """Check if a visit to a site is feasible given arrival time and visit duration.

    Returns (feasible, info_dict) where info_dict contains:
    - "remaining_minutes": minutes left in the open window
    - "closing_time": the close time of the current window
    - "opens_after": minutes until the site re-opens, if currently closed
    """
    schedule = load_site_schedule(db, site_id)
    is_open = schedule.is_open_at(arrival_time)

    if is_open:
        remaining = schedule.minutes_until_close(arrival_time)
        closing_arrival = arrival_time + timedelta(minutes=remaining)
        return True, {
            "feasible": remaining >= visit_minutes,
            "remaining_minutes": remaining,
            "closing_time": closing_arrival,
            "was_open": True,
        }
    else:
        # Site is closed; find when it next opens
        remaining = schedule.remaining_minutes(arrival_time)
        opens_after = remaining  # minutes until it opens
        # After it opens, we need visit_minutes
        feasible = (opens_after + visit_minutes) <= (24 * 60)  # simplistic
        return True, {
            "feasible": feasible,
            "remaining_minutes": 0,
            "closing_time": None,
            "was_open": False,
            "opens_after_minutes": opens_after,
            "opens_after": opens_after,
        }


# ─── Special schedule types ─────────────────────────────────────────────────

def has_split_slots(site_id: int, db) -> bool:
    """Check if a site has multiple open/close slots per day."""
    schedule = load_site_schedule(db, site_id)
    return len(schedule.slots) > 1


def is_closed_day(site_id: int, db, check_date: datetime) -> bool:
    """Check if a site is closed on a specific date/weekday.

    Note: This PRD assumes weekday-based scheduling; date-specific
    closures (e.g. festival days) would use site_restriction rows.
    """
    from ..db.models import SiteSchedule as SiteScheduleModel
    import pytz

    tz = pytz.timezone("Asia/Kolkata")
    check_weekday = check_date.astimezone(tz).strftime("%A")

    stmt = select(SiteScheduleModel).where(
        SiteScheduleModel.site_id == site_id,
        SiteScheduleModel.weekday == check_weekday,
    )
    result = db.execute(stmt)
    rows = result.scalars().all()

    # If no schedule row for this weekday, the site might be closed all day
    if not rows:
        # Check restrictions for specific dates
        return False  # default: assume open; restrictions handled separately

    # If all rows have close=open or some marker, it's a closed day
    for row in rows:
        if row.close is None or str(row.close).strip() == "":
            return True  # marked as closed day

    return False


# ─── Prayer time restrictions ───────────────────────────────────────────────

def has_prayer_restriction(site_id: int, db) -> bool:
    """Check if a site has prayer-time restrictions (e.g. mosques)."""
    from ..db.models import SiteRestriction as SiteRestrictionModel

    stmt = select(SiteRestrictionModel).where(SiteRestrictionModel.site_id == site_id)
    result = db.execute(stmt)
    rows = result.scalars().all()

    # Check if any restriction is a prayer window
    for row in rows:
        if row.reason and "prayer" in str(row.reason).lower():
            return True
    return False


def get_prayer_windows(site_id: int, db) -> List[dict]:
    """Get prayer time windows for a site, if any."""
    from ..db.models import SiteRestriction as SiteRestrictionModel

    stmt = select(SiteRestrictionModel).where(
        SiteRestrictionModel.site_id == site_id,
    )
    result = db.execute(stmt)
    rows = result.scalars().all()

    windows = []
    for row in rows:
        if row.reason and "prayer" in str(row.reason).lower():
            # Parse start/end times from the restriction
            windows.append({
                "start": str(row.start) if row.start else None,
                "end": str(row.end) if row.end else None,
                "reason": row.reason,
            })
    return windows
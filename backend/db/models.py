"""Virasat database models.

SQLAlchemy models for the heritage walk planner.
Uses simple float coordinates (lat/lng) instead of PostGIS geometry
to avoid dependency issues while still supporting spatial queries.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text,
    JSON,
    Index,
    ForeignKey,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ─── Timezone helper ────────────────────────────────────────────────────────

UTC = timezone.utc


# ─── City entity ────────────────────────────────────────────────────────────

class City(Base):
    """Represents a geographical coverage area (city)."""

    __tablename__ = "city"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    timezone = Column(String(50), nullable=False, default="Asia/Kolkata")
    bounds = Column(JSON, nullable=True)  # GeoJSON polygon boundary

    # Relationships
    sites = relationship("Site", back_populates="city", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"City(id={self.id}, name={self.name})"


# ─── Heritage site ─────────────────────────────────────────────────────────

class Site(Base):
    """A heritage site that can be included in a walk plan."""

    __tablename__ = "site"

    id = Column(Integer, primary_key=True)
    city_id = Column(Integer, ForeignKey("city.id"), nullable=False)
    name = Column(String(200), nullable=False)
    summary = Column(Text, nullable=True)  # Short description
    why_it_matters = Column(Text, nullable=True)  # Architectural/cultural significance
    dress_notes = Column(Text, nullable=True)  # Cultural etiquette/restrictions
    visit_minutes = Column(Integer, nullable=False, default=30)  # Typical visit duration
    categories = Column(JSON, nullable=True)  # List of category tags
    hidden_tier = Column(Boolean, nullable=False, default=False)  # Hidden/heritage tier
    status = Column(String(20), nullable=False, default="approved")  # approved, pending, rejected
    confidence = Column(String(10), nullable=False, default="high")  # high, medium, low

    # Coordinates: latitude and longitude as floats
    lat = Column(Float, nullable=False)  # Latitude
    lng = Column(Float, nullable=False)  # Longitude

    # Audit fields
    last_verified_on = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    city = relationship("City", back_populates="sites")
    schedules = relationship("SiteSchedule", back_populates="site", cascade="all, delete-orphan")
    sources = relationship("SiteSource", back_populates="site", cascade="all, delete-orphan")
    restrictions = relationship("SiteRestriction", back_populates="site", cascade="all, delete-orphan")
    submissions = relationship("Submission")
    problem_reports = relationship("ProblemReport", back_populates="affected_site")

    __table_args__ = (
        Index("ix_site_city_id", "city_id"),
        Index("ix_site_status_confidence", "status", "confidence"),
    )

    def __repr__(self) -> str:
        return f"Site(id={self.id}, name={self.name}, city_id={self.city_id})"


# ─── Site schedule ─────────────────────────────────────────────────────────

class SiteSchedule(Base):
    """Opening schedule for a heritage site, per weekday.

    Supports:
    - Multiple slots per day (split windows)
    - Different hours per weekday
    - Closed days (no rows for a weekday)
    - Restriction windows (prayer times, festival closures)
    """

    __tablename__ = "site_schedule"

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("site.id"), nullable=False)
    weekday = Column(String(20), nullable=False)  # Monday, Tuesday, etc.
    open = Column(String(5), nullable=True)  # HH:MM format
    close = Column(String(5), nullable=True)  # HH:MM format; None = closed all day

    # Relationship
    site = relationship("Site", back_populates="schedules")

    __table_args__ = (
        Index("ix_site_schedule_weekday", "site_id", "weekday"),
    )

    def __repr__(self) -> str:
        return f"SiteSchedule(id={self.id}, site_id={self.site_id}, weekday={self.weekday}, open={self.open}, close={self.close})"


# ─── Site source ───────────────────────────────────────────────────────────

class SiteSource(Base):
    """Source URL and metadata for a heritage site's information."""

    __tablename__ = "site_source"

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("site.id"), nullable=False)
    url = Column(String(500), nullable=False)
    title = Column(String(200), nullable=True)  # Title of the source page
    accessed_on = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationship
    site = relationship("Site", back_populates="sources")

    __table_args__ = (
        Index("ix_site_source_site_id", "site_id"),
    )

    def __repr__(self) -> str:
        return f"SiteSource(id={self.id}, site_id={self.site_id}, url={self.url[:40] if self.url else 'none'}...)"


# ─── Site restriction ──────────────────────────────────────────────────────

class SiteRestriction(Base):
    """Time-based or event-based restrictions on a site.

    Examples:
    - Prayer windows at mosques
    - Festival closures
    - Special event openings
    - Dress code days
    """

    __tablename__ = "site_restriction"

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("site.id"), nullable=False)
    weekday_or_date = Column(String(50), nullable=True)  # "Monday" or "2024-10-01"
    start = Column(String(5), nullable=True)  # HH:MM
    end = Column(String(5), nullable=True)  # HH:MM
    reason = Column(String(200), nullable=True)  # e.g. "Friday prayer", "Durga Puja"

    # Relationship
    site = relationship("Site", back_populates="restrictions")

    __table_args__ = (
        Index("ix_site_restriction_site_id", "site_id"),
        Index("ix_site_restriction_weekday", "weekday_or_date"),
    )

    def __repr__(self) -> str:
        return f"SiteRestriction(id={self.id}, site_id={self.site_id}, reason={self.reason})"


# ─── User ──────────────────────────────────────────────────────────────────

class User(Base):
    """Application user with roles."""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    email = Column(String(200), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="visitor")  # visitor, contributor, moderator
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    routes = relationship("Route", back_populates="owner")
    submissions = relationship("Submission", back_populates="submitter")
    problem_reports = relationship("ProblemReport", back_populates="reporter")
    shared_routes = relationship("Route", secondary="route_share", back_populates="shared_with")

    __table_args__ = (
        Index("ix_user_email", "email"),
        Index("ix_user_role", "role"),
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email}, role={self.role})"


# ─── Route ─────────────────────────────────────────────────────────────────

class Route(Base):
    """A saved heritage walk plan with its inputs and results."""

    __tablename__ = "route"

    id = Column(Integer, primary_key=True)
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=True)  # NULL for anonymous/shares
    share_token = Column(String(64), nullable=True, unique=True)  # Read-only share link
    inputs = Column(JSON, nullable=False)  # Serialized plan request
    result = Column(JSON, nullable=True)  # Serialized plan result
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    owner = relationship("User", back_populates="routes")
    shared_with = relationship("User", secondary="route_share", back_populates="shared_routes")

    __table_args__ = (
        Index("ix_route_owner_id", "owner_id"),
        Index("ix_route_share_token", "share_token"),
    )

    def __repr__(self) -> str:
        return f"Route(id={self.id}, owner_id={self.owner_id}, share_token={self.share_token[:8] if self.share_token else 'none'}...)"


# ─── Route share ────────────────────────

class RouteShare(Base):
    """Many-to-many link between routes and users who have access."""

    __tablename__ = "route_share"

    route_id = Column(Integer, ForeignKey("route.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    granted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    route = relationship("Route")
    user = relationship("User")

    __table_args__ = (
        Index("ix_route_share_route_id", "route_id"),
    )


# ─── Submission ────────────────────────────────────────────────────────────

class Submission(Base):
    """A community-submitted heritage site proposal."""

    __tablename__ = "submission"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)  # Can be anonymous
    site_id = Column(Integer, ForeignKey("site.id"), nullable=True)  # Proposed site, nullable for general proposals
    status = Column(String(20), nullable=False, default="pending")  # pending, approved, rejected, changes_requested
    proposed_data = Column(JSON, nullable=False)  # All fields proposed by contributor
    moderator_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    submitter = relationship("User", foreign_keys=[user_id], back_populates="submissions")
    proposed_site = relationship("Site", back_populates="submissions")

    __table_args__ = (
        Index("ix_submission_status", "status"),
        Index("ix_submission_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"Submission(id={self.id}, status={self.status}, user_id={self.user_id})"


# ─── Problem report ────────────────────────────────────────────────────────

class ProblemReport(Base):
    """A report about a heritage site issue (closed, wrong timings, etc.)."""

    __tablename__ = "problem_report"

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("site.id"), nullable=False)
    reporter_id = Column(Integer, ForeignKey("user.id"), nullable=True)  # None if anonymous
    report_type = Column(String(50), nullable=False)  # closed, wrong_timings, moved, inaccessible, other
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    status = Column(String(20), nullable=False, default="pending")  # pending, reviewed, resolved
    moderator_note = Column(Text, nullable=True)

    # Relationships
    affected_site = relationship("Site", foreign_keys=[site_id], back_populates="problem_reports")
    reporter = relationship("User", foreign_keys=[reporter_id])

    __table_args__ = (
        Index("ix_problem_report_site_id", "site_id"),
        Index("ix_problem_report_status", "status"),
        Index("ix_problem_report_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"ProblemReport(id={self.id}, site_id={self.site_id}, type={self.report_type})"
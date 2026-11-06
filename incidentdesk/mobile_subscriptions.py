"""Mobile alert subscriptions."""

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from incidentdesk.db import Base


class MobileSubscription(Base):
    __tablename__ = "mobile_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    engineer: Mapped[str] = mapped_column(String(80))
    services: Mapped[list[str]] = mapped_column(JSON)
    min_priority: Mapped[str] = mapped_column(String(2))

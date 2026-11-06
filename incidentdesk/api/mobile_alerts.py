"""/mobile/v1/subscriptions"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from incidentdesk.db import get_session
from incidentdesk.models import Service
from incidentdesk.mobile_subscriptions import MobileSubscription

router = APIRouter(prefix="/mobile/v1", tags=["mobile"])


class SubscriptionIn(BaseModel):
    engineer: str
    services: list[str]
    min_priority: Literal["P1", "P2", "P3", "P4"]


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    engineer: str
    services: list[str]
    min_priority: str


@router.post("/subscriptions", response_model=SubscriptionOut, status_code=201)
def create_subscription(body: SubscriptionIn, session: Session = Depends(get_session)):
    known_services = set(session.scalars(select(Service.slug).where(Service.slug.in_(body.services))))
    unknown_services = [service for service in body.services if service not in known_services]
    if unknown_services:
        raise HTTPException(422, f"Unknown service {unknown_services[0]}")

    subscription = MobileSubscription(**body.model_dump())
    session.add(subscription)
    session.commit()
    return subscription


@router.get("/subscriptions", response_model=list[SubscriptionOut])
def list_subscriptions(engineer: str, session: Session = Depends(get_session)):
    query = select(MobileSubscription).where(MobileSubscription.engineer == engineer).order_by(MobileSubscription.id)
    return list(session.scalars(query))

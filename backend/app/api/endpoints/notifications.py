from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...models.notification import Notification
from ...models import User
from ...schemas.notification_schema import NotificationRead
from ..endpoints.auth import get_current_active_user

router = APIRouter()

@router.get("/notifications", response_model=List[NotificationRead])
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()
    return notifications

@router.put("/notifications/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    if notification:
        notification.is_read = True
        db.commit()
    return {"message": "Okundu"}

@router.get("/notifications/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()
    return {"unread_count": count}
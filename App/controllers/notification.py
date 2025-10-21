from typing import List, Optional
from App.extensions import db
from App.models.notification import Notification
from App.models.street import Street
from App.models.user import User
from App.models.enums import NotificationType, NotificationCategory, NotificationPriority
import datetime as dt

'''
CREATE
'''
def create_notification(
    message: str,
    notification_type: NotificationType,
    street: Street | None = None,
    title: str | None = None,
    recipient: User | None = None,
    category: NotificationCategory | None = None,
    priority: NotificationPriority | None = None,
    expires_in_hours: int | None = None
) -> Notification:
    """
    Persist and return a Notification object with enhanced features.
    Maintains backward compatibility with old signature.
    Note: expires_in_hours parameter is deprecated and ignored.
    """
    # Generate title if not provided (backward compatibility)
    if title is None:
        title = _generate_title_from_type_and_message(notification_type, message)

    notif = Notification(
        title=title,
        message=message,
        notification_type=notification_type,
        recipient=recipient,
        street=street,
        category=category,
        priority=priority
    )
    db.session.add(notif)
    db.session.commit()
    return notif


def create_user_notification(
    title: str,
    message: str,
    recipient: User,
    notification_type: NotificationType = NotificationType.SYSTEM,
    category: NotificationCategory = NotificationCategory.GENERAL,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    expires_in_hours: int | None = None
) -> Notification:
    """
    Create a notification for a specific user.
    """
    return create_notification(
        title=title,
        message=message,
        notification_type=notification_type,
        recipient=recipient,
        category=category,
        priority=priority,
        expires_in_hours=expires_in_hours
    )


def create_street_notification(
    title: str,
    message: str,
    street: Street,
    notification_type: NotificationType = NotificationType.SCHEDULE,
    category: NotificationCategory = NotificationCategory.SCHEDULE,
    priority: NotificationPriority = NotificationPriority.NORMAL,
    expires_in_hours: int | None = 168  # 1 week default
) -> Notification:
    """
    Create a notification for all residents of a street.
    """
    return create_notification(
        title=title,
        message=message,
        notification_type=notification_type,
        street=street,
        category=category,
        priority=priority,
        expires_in_hours=expires_in_hours
    )


def create_system_notification(
    title: str,
    message: str,
    category: NotificationCategory = NotificationCategory.SYSTEM,
    priority: NotificationPriority = NotificationPriority.HIGH,
    expires_in_hours: int | None = 24  # 1 day default
) -> Notification:
    """
    Create a system-wide notification for all users.
    """
    return create_notification(
        title=title,
        message=message,
        notification_type=NotificationType.SYSTEM,
        category=category,
        priority=priority,
        expires_in_hours=expires_in_hours
    )


def _generate_title_from_type_and_message(notification_type: NotificationType, message: str) -> str:
    """Generate a title based on notification type for backward compatibility"""
    title_map = {
        NotificationType.NEW: "New Stop Scheduled",
        NotificationType.CONFIRMED: "Stop Confirmed",
        NotificationType.CANCELLED: "Stop Cancelled",
        NotificationType.COMPLETED: "Stop Completed",
        NotificationType.SCHEDULE: "Schedule Update",
        NotificationType.SYSTEM: "System Notification",
        NotificationType.STOP_REQUEST: "Stop Request"
    }

    # Try to get a descriptive title from the message if it's short
    if len(message) < 50 and not message.startswith('['):
        return message[:47] + '...' if len(message) > 47 else message

    return title_map.get(notification_type, "Notification")

'''
GET
'''
def get_notifications_by_street(street: Street, include_expired: bool = False) -> List[Notification]:
    """
    Return all notifications for a given Street (newest first).
    """
    stmt = db.select(Notification).where(Notification.street_name == street.name)

    # Filter out expired notifications unless explicitly requested
    if not include_expired:
        stmt = stmt.where(
            db.or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > dt.datetime.utcnow()
            )
        )

    stmt = stmt.order_by(Notification.created_at.desc())
    return list(db.session.execute(stmt).scalars().all())


def get_notifications_by_type(
    street: Street,
    notification_type: NotificationType,
    include_expired: bool = False
) -> List[Notification]:
    """
    Return notifications for a given Street and NotificationType (newest first).
    """
    stmt = db.select(Notification).where(
        Notification.street_name == street.name,
        Notification.type == notification_type.value,
    )

    # Filter out expired notifications unless explicitly requested
    if not include_expired:
        stmt = stmt.where(
            db.or_(
                Notification.expires_at.is_(None),
                Notification.expires_at > dt.datetime.utcnow()
            )
        )

    stmt = stmt.order_by(Notification.created_at.desc())
    return list(db.session.execute(stmt).scalars().all())


def get_notifications_by_user(
    user: User,
    include_global: bool = True,
    unread_only: bool = False,
    limit: int = 50
) -> List[Notification]:
    """
    Get notifications for a specific user including global and street-specific ones.
    """
    conditions = [Notification.recipient_id == user.id]

    # Include global notifications if requested
    if include_global:
        global_conditions = [Notification.is_global == True]

        # Add street-specific global notifications for residents
        if hasattr(user, 'street_name') and user.street_name:
            global_conditions.append(
                db.and_(
                    Notification.street_name == user.street_name,
                    Notification.recipient_id.is_(None)
                )
            )

        conditions.append(db.or_(*global_conditions))

    stmt = db.select(Notification).where(db.or_(*conditions))

    # Filter by read status
    if unread_only:
        stmt = stmt.where(Notification.is_read == False)

    # Exclude expired notifications
    stmt = stmt.where(
        db.or_(
            Notification.expires_at.is_(None),
            Notification.expires_at > dt.datetime.utcnow()
        )
    )

    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
    return list(db.session.execute(stmt).scalars().all())


def get_unread_count(user: User, include_global: bool = True) -> int:
    """Get count of unread notifications for a user"""
    conditions = [
        Notification.recipient_id == user.id,
        Notification.is_read == False
    ]

    if include_global:
        global_conditions = [Notification.is_global == True]

        if hasattr(user, 'street_name') and user.street_name:
            global_conditions.append(
                db.and_(
                    Notification.street_name == user.street_name,
                    Notification.recipient_id.is_(None)
                )
            )

        conditions.append(db.or_(*global_conditions))

    stmt = db.select(db.func.count(Notification.id)).where(
        db.and_(*conditions),
        db.or_(
            Notification.expires_at.is_(None),
            Notification.expires_at > dt.datetime.utcnow()
        )
    )

    return db.session.scalar(stmt) or 0


def mark_notification_as_read(notification_id: int, user: Optional[User] = None) -> bool:
    """Mark a notification as read"""
    notification = db.session.get(Notification, notification_id)
    if not notification:
        return False

    # Check permissions if user is provided
    if user and notification.recipient_id and notification.recipient_id != user.id:
        return False

    return notification.mark_as_read()


def mark_all_notifications_as_read(user: User) -> int:
    """Mark all unread notifications as read for a user"""
    notifications = get_notifications_by_user(
        user=user,
        include_global=True,
        unread_only=True,
        limit=1000
    )

    count = 0
    for notification in notifications:
        if notification.mark_as_read():
            count += 1

    return count


def cleanup_expired_notifications() -> int:
    """Delete expired notifications"""
    try:
        expired_notifications = db.session.execute(
            db.select(Notification).where(
                Notification.expires_at < dt.datetime.utcnow()
            )
        ).scalars().all()

        count = len(expired_notifications)
        for notification in expired_notifications:
            db.session.delete(notification)

        db.session.commit()
        return count
    except Exception:
        db.session.rollback()
        return 0

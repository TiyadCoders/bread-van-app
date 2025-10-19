from App.extensions import db
from .street import Street
from .enums import NotificationType, NotificationPriority, NotificationCategory
import datetime as dt
from typing import TYPE_CHECKING, Optional
from sqlalchemy import Index

if TYPE_CHECKING:
    from .user import User

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(20), nullable=False, default='general')
    priority = db.Column(db.String(10), nullable=False, default='normal')

    # Content fields
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)  # Changed to Text for longer messages

    # Recipient and context
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # null for global notifications
    recipient_type = db.Column(db.String(20), nullable=True)  # 'driver', 'resident', 'all'
    street_name = db.Column(db.String(255), nullable=True)

    # Status and metadata
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    is_global = db.Column(db.Boolean, nullable=False, default=False)  # Global vs targeted notification

    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    recipient = db.relationship('User', backref='notifications', lazy='joined')

    # Indexes for performance
    __table_args__ = (
        Index('idx_notifications_recipient', 'recipient_id', 'is_read'),
        Index('idx_notifications_street', 'street_name', 'created_at'),
        Index('idx_notifications_type', 'type', 'created_at'),
    )

    def __init__(
        self,
        title: str,
        message: str,
        notification_type: NotificationType,
        recipient: Optional['User'] = None,
        street: Optional[Street] = None,
        category: Optional[NotificationCategory] = None,
        priority: Optional[NotificationPriority] = None,
        expires_at: Optional[dt.datetime] = None
    ):
        self.title = title
        self.message = message
        self.type = notification_type.value
        self.category = (category or NotificationCategory.GENERAL).value
        self.priority = (priority or NotificationPriority.NORMAL).value

        # Recipient handling
        if recipient:
            self.recipient_id = recipient.id
            self.recipient_type = recipient.type
            self.is_global = False
        else:
            self.recipient_id = None
            self.recipient_type = None
            self.is_global = True

        # Street context
        if street:
            self.street_name = street.name

        # Timestamps
        self.created_at = dt.datetime.utcnow()
        self.expires_at = expires_at
        self.is_read = False

    def mark_as_read(self) -> bool:
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = dt.datetime.utcnow()
            try:
                db.session.add(self)
                db.session.commit()
                return True
            except Exception:
                db.session.rollback()
                return False
        return True

    def is_expired(self) -> bool:
        """Check if notification has expired"""
        if self.expires_at:
            return dt.datetime.utcnow() > self.expires_at
        return False

    def get_age_in_minutes(self) -> int:
        """Get notification age in minutes"""
        return int((dt.datetime.utcnow() - self.created_at).total_seconds() / 60)

    def get_json(self) -> dict:
        return {
            'id': self.id,
            'type': self.type,
            'category': self.category,
            'priority': self.priority,
            'title': self.title,
            'message': self.message,
            'streetName': self.street_name,
            'recipientId': self.recipient_id,
            'recipientType': self.recipient_type,
            'isRead': self.is_read,
            'isGlobal': self.is_global,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'readAt': self.read_at.isoformat() if self.read_at else None,
            'expiresAt': self.expires_at.isoformat() if self.expires_at else None,
            'isExpired': self.is_expired(),
            'ageInMinutes': self.get_age_in_minutes()
        }

    def to_api_dict(self) -> dict:
        """Enhanced API serialization for notifications"""
        return {
            'id': self.id,
            'type': self.type,
            'category': self.category,
            'priority': self.priority,
            'title': self.title,
            'message': self.message,
            'streetName': self.street_name,
            'recipient': {
                'id': self.recipient.id,
                'name': self.recipient.get_fullname(),
                'type': self.recipient.type
            } if self.recipient else None,
            'isRead': self.is_read,
            'isGlobal': self.is_global,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'readAt': self.read_at.isoformat() if self.read_at else None,
            'expiresAt': self.expires_at.isoformat() if self.expires_at else None,
            'isExpired': self.is_expired(),
            'ageInMinutes': self.get_age_in_minutes(),
            'formattedCreatedAt': self.format_created_at()
        }

    def format_created_at(self) -> str:
        """Format created_at for display"""
        if not self.created_at:
            return ""

        now = dt.datetime.utcnow()
        diff = now - self.created_at

        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"

    def to_string(self):
        return f"[Created {self.created_at}]\t{self.message}"

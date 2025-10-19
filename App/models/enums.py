from enum import Enum

class DriverStatus(Enum):
    INACTIVE: str = "inactive"
    EN_ROUTE: str = "en_route"
    DELIVERING: str = "delivering"

class NotificationType(Enum):
    ARRIVED: str = "arrived"
    REQUESTED: str = "requested"
    CONFIRMED: str = "confirmed"
    CANCELLED: str = "cancelled"
    DELAYED: str = "delayed"
    REMINDER: str = "reminder"
    ALERT: str = "alert"
    UPDATE: str = "update"
    SYSTEM: str = "system"
    NEW: str = "new"
    COMPLETED: str = "completed"
    SCHEDULE: str = "schedule"
    STOP_REQUEST: str = "stop_request"


class NotificationCategory(Enum):
    STOP_MANAGEMENT: str = "stop_management"
    DRIVER_STATUS: str = "driver_status"
    SYSTEM_ALERT: str = "system_alert"
    USER_UPDATE: str = "user_update"
    GENERAL: str = "general"
    SCHEDULE: str = "schedule"
    SERVICE: str = "service"
    SYSTEM: str = "system"


class NotificationPriority(Enum):
    LOW: str = "low"
    NORMAL: str = "normal"
    HIGH: str = "high"
    URGENT: str = "urgent"

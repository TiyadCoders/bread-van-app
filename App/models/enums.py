from enum import Enum

class DriverStatus(Enum):
    INACTIVE: str = "inactive"
    EN_ROUTE: str = "en_route"
    DELIVERING: str = "delivering"

class NotificationType(Enum):
    ARRIVED: str = "arrived"
    REQUESTED: str = "requested"
    CONFIRMED: str = "confirmed"

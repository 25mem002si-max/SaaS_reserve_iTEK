from enum import Enum


class UserRole(str, Enum):
    CLIENT = "client"
    MANAGER = "manager"
    ADMIN = "admin"
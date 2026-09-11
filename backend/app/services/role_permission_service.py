"""Minimal role-permission mapping for platform manifest."""

from enum import Enum


class Role(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    RESEARCHER = "researcher"
    ADMIN = "admin"


class Permission(str, Enum):
    READ = "read"
    ANALYZE = "analyze"
    EXPORT = "export"
    ADMIN = "admin"


ROLE_PERMISSIONS = {
    Role.VIEWER: [Permission.READ],
    Role.ANALYST: [Permission.READ, Permission.ANALYZE],
    Role.RESEARCHER: [Permission.READ, Permission.ANALYZE, Permission.EXPORT],
    Role.ADMIN: [Permission.READ, Permission.ANALYZE, Permission.EXPORT, Permission.ADMIN],
}

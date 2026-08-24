from typing import Optional, Dict, Any, List, Set
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Role(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    RESEARCHER = "researcher"
    TRADER = "trader"
    ADMIN = "admin"


class Permission(str, Enum):
    # Stock permissions
    VIEW_STOCK = "view_stock"
    SEARCH_STOCK = "search_stock"

    # Recommendation permissions
    VIEW_RECOMMENDATION = "view_recommendation"
    GENERATE_RECOMMENDATION = "generate_recommendation"
    MANAGE_RECOMMENDATION = "manage_recommendation"

    # Model permissions
    VIEW_MODEL = "view_model"
    TRAIN_MODEL = "train_model"
    APPROVE_MODEL = "approve_model"
    DEPLOY_MODEL = "deploy_model"

    # Portfolio permissions
    VIEW_PORTFOLIO = "view_portfolio"
    MANAGE_PORTFOLIO = "manage_portfolio"

    # User permissions
    VIEW_USERS = "view_users"
    MANAGE_USERS = "manage_users"

    # System permissions
    VIEW_AUDIT = "view_audit"
    MANAGE_SYSTEM = "manage_system"


# Role-Permission mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        Permission.VIEW_STOCK,
        Permission.VIEW_RECOMMENDATION,
        Permission.VIEW_PORTFOLIO,
    },
    Role.ANALYST: {
        Permission.VIEW_STOCK,
        Permission.SEARCH_STOCK,
        Permission.VIEW_RECOMMENDATION,
        Permission.GENERATE_RECOMMENDATION,
        Permission.VIEW_MODEL,
        Permission.VIEW_PORTFOLIO,
    },
    Role.RESEARCHER: {
        Permission.VIEW_STOCK,
        Permission.SEARCH_STOCK,
        Permission.VIEW_RECOMMENDATION,
        Permission.GENERATE_RECOMMENDATION,
        Permission.MANAGE_RECOMMENDATION,
        Permission.VIEW_MODEL,
        Permission.TRAIN_MODEL,
        Permission.VIEW_PORTFOLIO,
        Permission.MANAGE_PORTFOLIO,
    },
    Role.TRADER: {
        Permission.VIEW_STOCK,
        Permission.SEARCH_STOCK,
        Permission.VIEW_RECOMMENDATION,
        Permission.GENERATE_RECOMMENDATION,
        Permission.VIEW_MODEL,
        Permission.VIEW_PORTFOLIO,
        Permission.MANAGE_PORTFOLIO,
    },
    Role.ADMIN: {
        Permission.VIEW_STOCK,
        Permission.SEARCH_STOCK,
        Permission.VIEW_RECOMMENDATION,
        Permission.GENERATE_RECOMMENDATION,
        Permission.MANAGE_RECOMMENDATION,
        Permission.VIEW_MODEL,
        Permission.TRAIN_MODEL,
        Permission.APPROVE_MODEL,
        Permission.DEPLOY_MODEL,
        Permission.VIEW_PORTFOLIO,
        Permission.MANAGE_PORTFOLIO,
        Permission.VIEW_USERS,
        Permission.MANAGE_USERS,
        Permission.VIEW_AUDIT,
        Permission.MANAGE_SYSTEM,
    },
}


class RolePermissionService:
    """Service for role and permission management."""

    def __init__(self):
        # In-memory user-role mapping (would use database in production)
        self.user_roles: Dict[str, Role] = {}

    def assign_role(
        self,
        user_id: str,
        role: Role,
        assigned_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Assign a role to a user."""
        self.user_roles[user_id] = role

        return {
            "user_id": user_id,
            "role": role.value,
            "permissions": [p.value for p in ROLE_PERMISSIONS.get(role, set())],
            "assigned_by": assigned_by,
            "assigned_at": datetime.utcnow().isoformat(),
        }

    def get_user_role(self, user_id: str) -> Optional[Role]:
        """Get user's role."""
        return self.user_roles.get(user_id)

    def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get user's permissions."""
        role = self.get_user_role(user_id)
        if not role:
            return set()
        return ROLE_PERMISSIONS.get(role, set())

    def has_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has a specific permission."""
        permissions = self.get_user_permissions(user_id)
        return permission in permissions

    def has_any_permission(self, user_id: str, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        user_permissions = self.get_user_permissions(user_id)
        return any(p in user_permissions for p in permissions)

    def has_all_permissions(self, user_id: str, permissions: List[Permission]) -> bool:
        """Check if user has all specified permissions."""
        user_permissions = self.get_user_permissions(user_id)
        return all(p in user_permissions for p in permissions)

    def get_role_permissions(self, role: Role) -> List[str]:
        """Get permissions for a role."""
        permissions = ROLE_PERMISSIONS.get(role, set())
        return [p.value for p in permissions]

    def get_all_roles(self) -> List[Dict[str, Any]]:
        """Get all roles with their permissions."""
        return [
            {
                "role": role.value,
                "permissions": [p.value for p in permissions],
            }
            for role, permissions in ROLE_PERMISSIONS.items()
        ]

    def get_users_by_role(self, role: Role) -> List[str]:
        """Get all users with a specific role."""
        return [
            user_id for user_id, user_role in self.user_roles.items()
            if user_role == role
        ]

    def remove_role(
        self,
        user_id: str,
        removed_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Remove role from user."""
        if user_id in self.user_roles:
            del self.user_roles[user_id]

        return {
            "user_id": user_id,
            "removed_by": removed_by,
            "removed_at": datetime.utcnow().isoformat(),
        }

    def check_access(
        self,
        user_id: str,
        resource_type: str,
        action: str,
    ) -> Dict[str, Any]:
        """Check if user can perform action on resource."""
        # Map resource/action to permission
        permission_map = {
            ("stock", "view"): Permission.VIEW_STOCK,
            ("stock", "search"): Permission.SEARCH_STOCK,
            ("recommendation", "view"): Permission.VIEW_RECOMMENDATION,
            ("recommendation", "generate"): Permission.GENERATE_RECOMMENDATION,
            ("recommendation", "manage"): Permission.MANAGE_RECOMMENDATION,
            ("model", "view"): Permission.VIEW_MODEL,
            ("model", "train"): Permission.TRAIN_MODEL,
            ("model", "approve"): Permission.APPROVE_MODEL,
            ("model", "deploy"): Permission.DEPLOY_MODEL,
            ("portfolio", "view"): Permission.VIEW_PORTFOLIO,
            ("portfolio", "manage"): Permission.MANAGE_PORTFOLIO,
            ("user", "view"): Permission.VIEW_USERS,
            ("user", "manage"): Permission.MANAGE_USERS,
            ("audit", "view"): Permission.VIEW_AUDIT,
            ("system", "manage"): Permission.MANAGE_SYSTEM,
        }

        required_permission = permission_map.get((resource_type, action))

        if not required_permission:
            return {
                "allowed": False,
                "reason": f"Unknown resource/action: {resource_type}/{action}",
            }

        has_permission = self.has_permission(user_id, required_permission)

        return {
            "allowed": has_permission,
            "user_id": user_id,
            "resource_type": resource_type,
            "action": action,
            "required_permission": required_permission.value,
        }


# Global service instance
role_permission_service = RolePermissionService()

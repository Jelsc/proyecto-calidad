from rest_framework.permissions import BasePermission


class HasCyberShieldRole(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser or user.is_staff:
            return True

        return user.groups.filter(name__in=self.allowed_roles).exists()


class IsAnalystOrAdmin(HasCyberShieldRole):
    allowed_roles = ("admin", "analyst")


class IsOperatorOrAdmin(HasCyberShieldRole):
    allowed_roles = ("admin", "operator")

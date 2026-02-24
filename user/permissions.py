from rest_framework import permissions
from .models import User


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.is_staff and
            request.user.admin_role == User.AdminRole.SUPER_ADMIN
        )

    
class IsSiteAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.is_staff and
            request.user.admin_role == User.AdminRole.SITE_ADMIN
        )


class IsSuperOrSiteAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.is_staff and
            request.user.admin_role in {
                User.AdminRole.SUPER_ADMIN,
                User.AdminRole.SITE_ADMIN,
            }
        )


class IsTicketOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user
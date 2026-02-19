from rest_framework.permissions import BasePermission

from user.models import User


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_staff
            and request.user.admin_role == User.AdminRole.SUPER_ADMIN
            # and request.user.admin_role in{ User.AdminRole.SUPER_ADMIN,
            #                                 User.AdminRole.SITE_ADMIN}
        )

class IsSiteAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_staff
            and request.user.admin_role == User.AdminRole.SITE_ADMIN
        )

class IsSuperOrSiteAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.is_staff
            and request.user.admin_role in {
                User.AdminRole.SUPER_ADMIN,
                User.AdminRole.SITE_ADMIN,
            }
        )



class IsTicketOwnerOrAdmin(BasePermission):
    """
    - User can access only their own tickets
    - Admins can access all
    """

    def has_object_permission(self, request, view, obj):

        if request.user.is_staff:
            return True

        return obj.user == request.user
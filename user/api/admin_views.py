from django.http import request
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from store.models import Order
from user.api.admin_models import Article, Media, Icon, AuditLog, IconCategory
from user.api.admin_user_serializer import UserAdminSerializer, ArticleSerializer, MediaSerializer, IconSerializer, \
    AuditLogSerializer, IconCategorySerializer
from user.models import User
from user.permissions import IsSuperOrSiteAdmin, IsSuperAdmin
from user.services.analytics import get_admin_kpis
from user.services.ordering import change_order_status


class AdminDashboardAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        data = get_admin_kpis()
        return Response(data)


class UserAdminViewSet(ModelViewSet):

    permission_classes = [IsSuperAdmin]
    serializer_class = UserAdminSerializer
    queryset = User.objects.all()

    @action(detail=True, methods=["post"])
    def change_role(self, request, pk=None):
        if request.user.admin_role != User.AdminRole.SUPER_ADMIN:
            raise PermissionDenied("Only super admins can change roles")

        user = self.get_object()
        user.admin_role = request.data.get("role")
        user.save()

        return Response({"detail": "Role updated"})



class AdminArticleViewSet(ModelViewSet):
    permission_classes = [IsSuperOrSiteAdmin]
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()


class AdminMediaViewSet(ModelViewSet):
    permission_classes = [IsSuperOrSiteAdmin]
    queryset = Media.objects.all()
    serializer = MediaSerializer( queryset, many=True,
                                  context={"request": request})


class AdminIconViewSet(ModelViewSet):
    permission_classes = [IsSuperOrSiteAdmin]
    queryset = Icon.objects.all()
    serializer_class = serializer = IconSerializer(
    queryset,
    many=True,
    context={"request": request}
)


class AdminIconCategoryViewSet(ModelViewSet):
    queryset = IconCategory.objects.all()
    serializer_class = IconCategorySerializer
    permission_classes = [IsSuperOrSiteAdmin]



class AdminOrderStatusAPIView(GenericAPIView):
    permission_classes = [IsSuperOrSiteAdmin]

    def post(self, request, pk):
        order = Order.objects.get(pk=pk)
        new_status = request.data["status"]

        change_order_status(
            order=order,
            new_status=new_status,
            user=request.user
        )

        return Response({"detail": "Status updated"})


class AuditLogViewSet(ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by("-created_at")
    permission_classes = [IsSuperAdmin]
    serializer_class = AuditLogSerializer


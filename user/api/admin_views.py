from django.http import request
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView, GenericAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from user.api.admin_models import Article, Media, Icon
from user.api.admin_user_serializer import AdminUserSerializer, ArticleSerializer, MediaSerializer, IconSerializer
from user.models import Order
from store.services.analytics import get_admin_kpis
from store.services.ordering import change_order_status
from user.models import User


class AdminDashboardAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        data = get_admin_kpis()
        return Response(data)

class AdminUserListAPIView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all()

class AdminUserDetailAPIView(RetrieveUpdateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = AdminUserSerializer
    queryset = User.objects.all()

class AdminArticleViewSet(ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = ArticleSerializer
    queryset = Article.objects.all()

class AdminMediaViewSet(ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Media.objects.all()
    serializer = MediaSerializer( queryset, many=True,
                                  context={"request": request})

class AdminIconViewSet(ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Icon.objects.all()
    serializer_class = serializer = IconSerializer(
    queryset,
    many=True,
    context={"request": request}
)

class AdminOrderStatusAPIView(GenericAPIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        order = Order.objects.get(pk=pk)
        new_status = request.data["status"]

        change_order_status(
            order=order,
            new_status=new_status,
            user=request.user
        )

        return Response({"detail": "Status updated"})

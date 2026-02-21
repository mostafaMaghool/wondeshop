from django.urls import path

from .api.admin_views import AdminDashboardAPIView, RevenueTrendAPIView, OrdersTrendAPIView
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("register/", RegisterAPIView.as_view()),

    path("login/", LoginAPIView.as_view()),

    path("profile/", UserProfileView.as_view()),

    path("profile_info/<int:pk>", profile_info),

    path('user/panel/', UserPanelAPIView.as_view(), name='user-panel'),

    path("admin/dashboard/", AdminDashboardAPIView.as_view()),
    path("admin/trends/revenue/", RevenueTrendAPIView.as_view()),
    path("admin/trends/orders/", OrdersTrendAPIView.as_view()),

    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),

    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

]

from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
# from 

urlpatterns = [
    path("register/", RegisterAPIView.as_view()),
    path("login/", LoginAPIView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("profile/", UserProfleView.as_view()),
    path("profile_info/<int:pk>", profile_info),
    path('user/panel/', UserPanelAPIView.as_view(), name='user-panel'),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('password-reset/request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

]

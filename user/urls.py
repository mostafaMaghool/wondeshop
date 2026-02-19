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
    # path("articles", ),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

]

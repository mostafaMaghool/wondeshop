from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("store.urls")),
    path('', include("user.urls")),
    path('api/token/', TokenObtainPairView.as_view(),name='token_obtsin'),
    path('api/token/refresh', TokenRefreshView.as_view(),name='token_refresh')
]

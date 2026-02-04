from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from . import views
from .views import *
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register('products', views.ProductView, basename='products')
router.register('product-images', views.ProductImageViewSet, basename='product-images')
router.register('categories', views.CategoryViewSet, basename='categories')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'cart/items', CartItemViewSet, basename='cart-item')

urlpatterns = [
    path('address/',views.AddressGenericApiView.as_view()),
    path('products/info/',views.product_info),
    path('api/schema/',SpectacularAPIView.as_view(),name='schema'),
    path('api/schema/swagger',SpectacularSwaggerView.as_view(url_name='schema'),name='swagger-ui'),
    path('orders/', views.OrdersGenericApiView.as_view()),
    path('orders/<int:pk>', views.OrdersGenericDetailView.as_view()),
    path('orderItems/', views.OrderItemsGenericApiView.as_view()),
    path('orderItems/<int:pk>', views.OrderItemsGenericDetailView.as_view()),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('password-reset/request/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]
urlpatterns += router.urls
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

from django.urls import path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.conf import settings
from django.conf.urls.static import static
from . import views

router = DefaultRouter()
router.register("products", views.ProductViewSet, basename="products")
router.register("product-images", views.ProductImageViewSet, basename="product-images")
router.register("categories", views.CategoryViewSet, basename="categories")
router.register(r"admin/products/search", views.AdminProductSearchViewSet, basename= "admin-product-search")

urlpatterns = [
    path("products/info/", views.product_info),

    path("address/", views.AddressGenericApiView.as_view()),
    path("address/<int:pk>/", views.AddressGenericDetailView.as_view()),

    path("orders/", views.OrdersGenericApiView.as_view()),
    path("orders/<int:pk>/", views.OrdersGenericDetailView.as_view()),

    path("order-items/", views.OrderItemsGenericApiView.as_view()),
    path("order-items/<int:pk>/", views.OrderItemsGenericDetailView.as_view()),

    path("search/", views.ProductSearchAPIView.as_view()),

    path("price-history/<int:pk>/", views.ProductPriceHistoryView.as_view()),

    path("change-password/", views.ChangePasswordView.as_view()),
    path("logout/", views.LogoutView.as_view()),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger/", SpectacularSwaggerView.as_view(url_name="schema")),
]

urlpatterns += router.urls

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

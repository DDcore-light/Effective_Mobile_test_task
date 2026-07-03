from django.urls import path

from business.views import (
    OrderDetailView,
    OrderListView,
    ProductDetailView,
    ProductListView,
    StoreDetailView,
    StoreListView,
)

urlpatterns = [
    path("products/", ProductListView.as_view(), name="products-list"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="products-detail"),
    path("stores/", StoreListView.as_view(), name="stores-list"),
    path("stores/<int:pk>/", StoreDetailView.as_view(), name="stores-detail"),
    path("orders/", OrderListView.as_view(), name="orders-list"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="orders-detail"),
]

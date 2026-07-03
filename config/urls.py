from django.urls import include, path

urlpatterns = [
    path("api/auth/", include("users.urls")),
    path("api/access-control/", include("access_control.urls")),
    path("api/business/", include("business.urls")),
]

from django.urls import path

from access_control.views import (
    AccessRuleDetailView,
    AccessRuleListView,
    BusinessElementListView,
    RoleListView,
)

urlpatterns = [
    path("roles/", RoleListView.as_view(), name="roles-list"),
    path("elements/", BusinessElementListView.as_view(), name="elements-list"),
    path("rules/", AccessRuleListView.as_view(), name="rules-list"),
    path("rules/<int:pk>/", AccessRuleDetailView.as_view(), name="rules-detail"),
]

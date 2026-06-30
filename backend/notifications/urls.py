from django.urls import path

from .views import (
    NotificationDetailView,
    NotificationSettingsView,
    NotificationView,
)


urlpatterns = [
    path(
        "",
        NotificationView.as_view(),
        name="notifications",
    ),

    path(
        "settings/",
        NotificationSettingsView.as_view(),
        name="notification-settings",
    ),

    path(
        "<int:notification_id>/",
        NotificationDetailView.as_view(),
        name="notification-detail",
    ),
]

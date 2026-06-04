from django.urls import path

from .views import DailyLogView


urlpatterns = [
    path("", DailyLogView.as_view(), name="daily-logs"),
]
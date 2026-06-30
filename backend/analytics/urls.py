from django.urls import path

from .views import AnalyticsMessageView, AnalyticsReportView


urlpatterns = [
    path(
        "reports/",
        AnalyticsReportView.as_view(),
        name="analytics-reports",
    ),

    path(
        "messages/",
        AnalyticsMessageView.as_view(),
        name="analytics-messages",
    ),
]

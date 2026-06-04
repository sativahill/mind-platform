from django.urls import path

from .views import WinView


urlpatterns = [
    path("", WinView.as_view(), name="wins"),
]
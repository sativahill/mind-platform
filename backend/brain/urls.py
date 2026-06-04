from django.urls import path

from .views import BrainView



urlpatterns = [
    path("", BrainView.as_view(), name="brain"),
]
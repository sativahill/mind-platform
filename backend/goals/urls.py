from django.urls import path

from .views import GoalView

urlpatterns = [
    path(
        "",
        GoalView.as_view(),
        name="goals",
    ),
]
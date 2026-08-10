from django.urls import path

from .views import (
    HabitArchiveView,
    HabitCompleteView,
    HabitDetailView,
    HabitMissView,
    HabitRestoreView,
    HabitView,
)


urlpatterns = [
    path(
        "",
        HabitView.as_view(),
        name="habit-list",
    ),
    path(
        "<int:habit_id>/",
        HabitDetailView.as_view(),
        name="habit-detail",
    ),
    path(
        "<int:habit_id>/complete/",
        HabitCompleteView.as_view(),
        name="habit-complete",
    ),
    path(
        "<int:habit_id>/miss/",
        HabitMissView.as_view(),
        name="habit-miss",
    ),
    path(
        "<int:habit_id>/archive/",
        HabitArchiveView.as_view(),
        name="habit-archive",
    ),
    path(
        "<int:habit_id>/restore/",
        HabitRestoreView.as_view(),
        name="habit-restore",
    ),
]
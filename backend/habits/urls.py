from django.urls import path

from .views import (
    HabitView,
    HabitCompleteView,
)

urlpatterns = [
    path(
        "",
        HabitView.as_view(),
        name="habits",
    ),

    path(
        "<int:habit_id>/complete/",
        HabitCompleteView.as_view(),
        name="habit-complete",
    ),
]
from django.urls import path

from .views import (
    BoardTaskView,
    BoardTaskDetailView,
)

urlpatterns = [
    path(
        "",
        BoardTaskView.as_view(),
        name="board",
    ),

    path(
        "<int:task_id>/",
        BoardTaskDetailView.as_view(),
        name="board-detail",
    ),
]
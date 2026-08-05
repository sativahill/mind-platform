from django.urls import path

from .views import (
    BoardTaskDetailView,
    BoardTaskLayoutView,
    BoardTaskView,
)


urlpatterns = [
    path(
        "",
        BoardTaskView.as_view(),
        name="board",
    ),
    path(
        "layout/",
        BoardTaskLayoutView.as_view(),
        name="board-layout",
    ),
    path(
        "<int:task_id>/",
        BoardTaskDetailView.as_view(),
        name="board-detail",
    ),
]
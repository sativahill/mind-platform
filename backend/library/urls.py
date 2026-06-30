from django.urls import path

from .views import BookDetailView, BookView


urlpatterns = [
    path(
        "",
        BookView.as_view(),
        name="library",
    ),

    path(
        "<int:book_id>/",
        BookDetailView.as_view(),
        name="library-detail",
    ),
]

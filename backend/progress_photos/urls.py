from django.urls import path

from .views import ProgressPhotoDetailView, ProgressPhotoView


urlpatterns = [
    path(
        "",
        ProgressPhotoView.as_view(),
        name="progress-photos",
    ),

    path(
        "<int:photo_id>/",
        ProgressPhotoDetailView.as_view(),
        name="progress-photo-detail",
    ),
]

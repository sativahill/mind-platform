from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ProgressPhoto
from .serializers import ProgressPhotoSerializer
from .services import update_brain_from_progress_photo


class ProgressPhotoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        photos = ProgressPhoto.objects.filter(
            user=request.user
        )

        serializer = ProgressPhotoSerializer(
            photos,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = ProgressPhotoSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        progress_photo = ProgressPhoto.objects.create(
            user=request.user,
            photo=serializer.validated_data["photo"],
            date=serializer.validated_data["date"],
            metrics=serializer.validated_data.get(
                "metrics",
                {},
            ),
            ai_analysis=serializer.validated_data.get(
                "ai_analysis",
                "",
            ),
        )

        update_brain_from_progress_photo(progress_photo)

        return Response(
            ProgressPhotoSerializer(progress_photo).data,
            status=201,
        )


class ProgressPhotoDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, photo_id):
        progress_photo = get_object_or_404(
            ProgressPhoto,
            id=photo_id,
            user=request.user,
        )

        serializer = ProgressPhotoSerializer(
            progress_photo,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        update_brain_from_progress_photo(progress_photo)

        return Response(serializer.data)

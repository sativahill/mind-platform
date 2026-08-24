from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    BrainSerializer,
    BrainUpdateSerializer,
)
from .services import update_brain_data


class BrainView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = BrainSerializer(
            request.user.brain
        )
        return Response(serializer.data)

    def post(self, request):
        if not isinstance(request.data, dict):
            return Response(
                {
                    "detail": (
                        "Request body must be a JSON object."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        update_serializer = BrainUpdateSerializer(
            data=request.data
        )
        update_serializer.is_valid(
            raise_exception=True
        )

        brain = update_brain_data(
            user=request.user,
            patch=(
                update_serializer
                .validated_data["data"]
            ),
        )
        return Response(
            BrainSerializer(brain).data
        )

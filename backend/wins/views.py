from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Win
from .serializers import WinSerializer
from .services import (
    create_manual_win,
    sync_brain_wins,
    update_brain_from_win,
)


class WinView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, request):
        queryset = Win.objects.filter(
            user=request.user
        )

        size = request.query_params.get(
            "size"
        )

        if size:
            valid_sizes = {
                Win.SMALL,
                Win.MEDIUM,
                Win.LARGE,
            }

            if size not in valid_sizes:
                return None

            queryset = queryset.filter(
                size=size
            )

        return queryset

    def get_win(self, request):
        win_id = request.query_params.get(
            "id"
        )

        if not win_id:
            return None

        return get_object_or_404(
            Win,
            id=win_id,
            user=request.user,
        )

    def get(self, request):
        win = self.get_win(request)

        if win is not None:
            serializer = WinSerializer(
                win,
                context={
                    "request": request
                },
            )

            return Response(
                serializer.data
            )

        queryset = self.get_queryset(
            request
        )

        if queryset is None:
            return Response(
                {
                    "size": [
                        (
                            "Choose small, "
                            "medium or large."
                        )
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WinSerializer(
            queryset,
            many=True,
            context={
                "request": request
            },
        )

        return Response(
            serializer.data
        )

    def post(self, request):
        serializer = WinSerializer(
            data=request.data,
            context={
                "request": request
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        win = create_manual_win(
            user=request.user,
            title=(
                serializer
                .validated_data["title"]
            ),
            description=(
                serializer
                .validated_data.get(
                    "description",
                    "",
                )
            ),
            date=(
                serializer
                .validated_data["date"]
            ),
            size=(
                serializer
                .validated_data["size"]
            ),
        )

        response_serializer = WinSerializer(
            win,
            context={
                "request": request
            },
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request):
        win = self.get_win(request)

        if win is None:
            return Response(
                {
                    "detail": (
                        "Provide the Win id "
                        "in the query parameters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WinSerializer(
            win,
            data=request.data,
            partial=True,
            context={
                "request": request
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_win = serializer.save()

        update_brain_from_win(
            updated_win
        )

        response_serializer = WinSerializer(
            updated_win,
            context={
                "request": request
            },
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        win = self.get_win(request)

        if win is None:
            return Response(
                {
                    "detail": (
                        "Provide the Win id "
                        "in the query parameters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = WinSerializer(
            win,
            data=request.data,
            context={
                "request": request
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_win = serializer.save()

        update_brain_from_win(
            updated_win
        )

        response_serializer = WinSerializer(
            updated_win,
            context={
                "request": request
            },
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        win = self.get_win(request)

        if win is None:
            return Response(
                {
                    "detail": (
                        "Provide the Win id "
                        "in the query parameters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        win.delete()

        sync_brain_wins(
            request.user
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )
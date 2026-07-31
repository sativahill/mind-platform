from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Goal
from .serializers import GoalSerializer
from .services import (
    sync_brain_goals,
    update_brain_from_goal,
)


class GoalView(APIView):
    permission_classes = [IsAuthenticated]

    def get_goal(self, request):
        goal_id = request.query_params.get(
            "id"
        )

        if not goal_id:
            return None

        return get_object_or_404(
            Goal,
            id=goal_id,
            user=request.user,
        )

    def get_queryset(self, request):
        queryset = Goal.objects.filter(
            user=request.user
        )

        goal_status = request.query_params.get(
            "status"
        )

        if goal_status:
            valid_statuses = {
                Goal.ACTIVE,
                Goal.COMPLETED,
                Goal.ARCHIVED,
            }

            if goal_status not in valid_statuses:
                return None

            queryset = queryset.filter(
                status=goal_status
            )

        return queryset

    def get(self, request):
        goal = self.get_goal(
            request
        )

        if goal is not None:
            serializer = GoalSerializer(
                goal,
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
                    "status": [
                        (
                            "Choose active, "
                            "completed or archived."
                        )
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = GoalSerializer(
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
        serializer = GoalSerializer(
            data=request.data,
            context={
                "request": request
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        goal = serializer.save(
            user=request.user
        )

        update_brain_from_goal(
            goal
        )

        response_serializer = GoalSerializer(
            goal,
            context={
                "request": request
            },
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request):
        goal = self.get_goal(
            request
        )

        if goal is None:
            return Response(
                {
                    "detail": (
                        "Provide the Goal id "
                        "in the query parameters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = GoalSerializer(
            goal,
            data=request.data,
            partial=True,
            context={
                "request": request
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_goal = serializer.save()

        update_brain_from_goal(
            updated_goal
        )

        response_serializer = GoalSerializer(
            updated_goal,
            context={
                "request": request
            },
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        goal = self.get_goal(
            request
        )

        if goal is None:
            return Response(
                {
                    "detail": (
                        "Provide the Goal id "
                        "in the query parameters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = GoalSerializer(
            goal,
            data=request.data,
            context={
                "request": request
            },
        )

        serializer.is_valid(
            raise_exception=True
        )

        updated_goal = serializer.save()

        update_brain_from_goal(
            updated_goal
        )

        response_serializer = GoalSerializer(
            updated_goal,
            context={
                "request": request
            },
        )

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        goal = self.get_goal(
            request
        )

        if goal is None:
            return Response(
                {
                    "detail": (
                        "Provide the Goal id "
                        "in the query parameters."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        goal.delete()

        sync_brain_goals(
            request.user
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )
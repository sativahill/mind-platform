from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goals.models import Goal
from goals.services import recalculate_goal_progress

from .models import BoardTask
from .serializers import BoardTaskSerializer


class BoardTaskView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = BoardTask.objects.filter(
            goal__user=request.user
        )

        serializer = BoardTaskSerializer(
            tasks,
            many=True,
        )

        return Response(
            serializer.data
        )

    def post(self, request):
        serializer = BoardTaskSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        goal = get_object_or_404(
            Goal,
            id=serializer.validated_data["goal"].id,
            user=request.user,
        )

        task = BoardTask.objects.create(
            goal=goal,
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get(
                "description",
                "",
            ),
            status=serializer.validated_data.get(
                "status",
                BoardTask.TODO,
            ),
        )

        recalculate_goal_progress(
            goal
        )

        return Response(
            BoardTaskSerializer(task).data,
            status=201,
        )


class BoardTaskDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, task_id):
        task = get_object_or_404(
            BoardTask,
            id=task_id,
            goal__user=request.user,
        )

        task_status = request.data.get(
            "status"
        )

        if task_status not in [
            BoardTask.TODO,
            BoardTask.IN_PROGRESS,
            BoardTask.DONE,
        ]:
            return Response(
                {
                    "detail": (
                        "Invalid status."
                    )
                },
                status=400,
            )

        task.status = task_status

        task.save(
            update_fields=[
                "status",
            ]
        )

        recalculate_goal_progress(
            task.goal
        )

        return Response(
            BoardTaskSerializer(task).data
        )
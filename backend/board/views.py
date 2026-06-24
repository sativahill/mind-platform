from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from goals.models import Goal

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

        return Response(serializer.data)

    def post(self, request):
        serializer = BoardTaskSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        goal = Goal.objects.get(
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

        status = request.data.get(
            "status"
        )

        if status not in [
            BoardTask.TODO,
            BoardTask.IN_PROGRESS,
            BoardTask.DONE,
        ]:
            return Response(
                {
                    "detail":
                    "Invalid status."
                },
                status=400,
            )

        task.status = status
        task.save()

        goal = task.goal

        total_tasks = BoardTask.objects.filter(
            goal=goal
        ).count()

        done_tasks = BoardTask.objects.filter(
            goal=goal,
            status=BoardTask.DONE,
        ).count()

        if total_tasks > 0:
            goal.progress = int(
                (done_tasks / total_tasks)
                * 100
            )
        else:
            goal.progress = 0

        goal.save()

        return Response(
            BoardTaskSerializer(task).data
        )
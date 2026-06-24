from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Goal
from .serializers import GoalSerializer


class GoalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        goals = Goal.objects.filter(
            user=request.user
        )

        serializer = GoalSerializer(
            goals,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = GoalSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        goal = Goal.objects.create(
            user=request.user,
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get(
                "description",
                "",
            ),
            status=serializer.validated_data.get(
                "status",
                Goal.ACTIVE,
            ),
            progress=serializer.validated_data.get(
                "progress",
                0,
            ),
        )

        return Response(
            GoalSerializer(goal).data,
            status=201,
        )
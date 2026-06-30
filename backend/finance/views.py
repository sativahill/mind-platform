from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FinanceGoal, FinanceTransaction
from .serializers import (
    FinanceGoalSerializer,
    FinanceTransactionSerializer,
)
from .services import update_brain_from_finance_goal


class FinanceGoalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        goals = FinanceGoal.objects.filter(
            user=request.user
        )

        serializer = FinanceGoalSerializer(
            goals,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = FinanceGoalSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        goal = FinanceGoal.objects.create(
            user=request.user,
            title=serializer.validated_data["title"],
            target_amount=serializer.validated_data["target_amount"],
            current_amount=serializer.validated_data.get(
                "current_amount",
                0,
            ),
            deadline=serializer.validated_data.get(
                "deadline",
            ),
        )

        update_brain_from_finance_goal(goal)

        return Response(
            FinanceGoalSerializer(goal).data,
            status=201,
        )


class FinanceTransactionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, goal_id):
        goal = get_object_or_404(
            FinanceGoal,
            id=goal_id,
            user=request.user,
        )

        transactions = FinanceTransaction.objects.filter(
            goal=goal
        )

        serializer = FinanceTransactionSerializer(
            transactions,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request, goal_id):
        goal = get_object_or_404(
            FinanceGoal,
            id=goal_id,
            user=request.user,
        )

        serializer = FinanceTransactionSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        transaction = FinanceTransaction.objects.create(
            goal=goal,
            amount=serializer.validated_data["amount"],
            note=serializer.validated_data.get(
                "note",
                "",
            ),
        )

        goal.current_amount = (
            goal.current_amount
            + transaction.amount
        )
        goal.save()

        update_brain_from_finance_goal(goal)

        return Response(
            FinanceTransactionSerializer(transaction).data,
            status=201,
        )

from django.urls import path

from .views import FinanceGoalView, FinanceTransactionView


urlpatterns = [
    path(
        "",
        FinanceGoalView.as_view(),
        name="finance",
    ),

    path(
        "<int:goal_id>/transactions/",
        FinanceTransactionView.as_view(),
        name="finance-transactions",
    ),
]

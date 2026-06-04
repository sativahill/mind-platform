from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from daily_logs.models import DailyLog
from wins.models import Win


class HomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        brain = request.user.brain

        daily_logs_count = DailyLog.objects.filter(
            user=request.user
        ).count()

        wins_count = Win.objects.filter(
            user=request.user
        ).count()

        last_win = Win.objects.filter(
            user=request.user
        ).first()

        last_daily_log = DailyLog.objects.filter(
            user=request.user
        ).first()

        return Response(
            {
                "last_daily_log": (
                    {
                        "date":str(last_daily_log.date),
                        "content": last_daily_log.content,
                    }
                    if last_daily_log
                    else None
                ),

                
                "brain": brain.data,
                "daily_logs_count": daily_logs_count,
                "wins_count": wins_count,
                "last_win": (
                    {
                        "title": last_win.title,
                        "size": last_win.size,
                    }
                    if last_win
                    else None
                ),
            }
        )
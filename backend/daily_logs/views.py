from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DailyLog
from .serializers import DailyLogSerializer
from .services import update_brain_from_daily_log


class DailyLogView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date = request.query_params.get("date")

        if date:
            try:
                log = DailyLog.objects.get(
                    user=request.user,
                    date=date,
                )

                serializer = DailyLogSerializer(log)

                return Response(serializer.data)

            except DailyLog.DoesNotExist:
                return Response(
                    {"detail": "Daily Log not found."},
                    status=404,
                )

        logs = DailyLog.objects.filter(
            user=request.user
        )

        serializer = DailyLogSerializer(
            logs,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = DailyLogSerializer(
            data=request.data,
            context={"request": request}
        )

        serializer.is_valid(
            raise_exception=True
        )

        daily_log = DailyLog.objects.create(
            user=request.user,
            date=serializer.validated_data["date"],
            content=serializer.validated_data["content"],
        )

        update_brain_from_daily_log(daily_log)

        return Response(
            DailyLogSerializer(daily_log).data,
            status=201
        )
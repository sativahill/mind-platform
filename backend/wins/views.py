from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Win
from .serializers import WinSerializer
from .services import update_brain_from_win


class WinView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wins = Win.objects.filter(
            user=request.user
        )

        serializer = WinSerializer(
            wins,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = WinSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        win = Win.objects.create(
            user=request.user,
            title=serializer.validated_data["title"],
            size=serializer.validated_data["size"],
        )

        update_brain_from_win(win)

        return Response(
            WinSerializer(win).data,
            status=201
        )
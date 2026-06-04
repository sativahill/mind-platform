from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework.permissions import IsAuthenticated

from .models import Brain
from .serializers import BrainSerializer
from .services import deep_merge_dict

class BrainView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        brain = request.user.brain

        serializer = BrainSerializer(brain)

        return Response(serializer.data)
    
    def post (self, request):
        brain = request.user.brain

        merged_data = deep_merge_dict(
            brain.data,
            request.data.get("data", {})
        )

        brain.data = merged_data
        brain.save()

        serializer = BrainSerializer(brain)

        return Response(serializer.data)
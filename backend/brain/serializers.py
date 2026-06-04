# import jango rest framework
from rest_framework import serializers
#"." из текущей памяти brain/models.py
from .models import Brain



class BrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brain
        fields = [
            "id",
            "data",
            "created_at",
            "updated_at",
        ]
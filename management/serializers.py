from rest_framework import serializers
from .models import Key


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model=Key
        fields = '__all__'

    def create(self, Kwargs):
        instance = Key.objects.create(**Kwargs)
        return instance



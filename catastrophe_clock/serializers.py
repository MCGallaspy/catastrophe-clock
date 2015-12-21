from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Catastrophe


class CatastropheSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Catastrophe
        fields = ('name', 'description', 'arrival_date', 'url', 'more_info', )


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ('username', 'is_staff', )

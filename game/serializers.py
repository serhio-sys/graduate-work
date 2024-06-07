from .models import Room
from users.models import NewUser
from rest_framework import serializers

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewUser
        fields = ['id', 'username', 'lvl']

class RoomSerializer(serializers.ModelSerializer):
    first_player = UserSerializer(read_only = True)

    class Meta:
        model = Room
        fields = ['id', 'first_player', 'name', 'rate', 'password']
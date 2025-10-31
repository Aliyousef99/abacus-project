from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Mantle

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user_id', 'username', 'display_name', 'role']
        extra_kwargs = {
            'display_name': { 'required': False, 'allow_blank': True }
        }

class MantleSerializer(serializers.ModelSerializer):
    heir_id = serializers.IntegerField(source='user.id', read_only=True)
    heir_username = serializers.CharField(source='user.username', read_only=True)
    granted_by_id = serializers.IntegerField(source='granted_by.id', read_only=True)
    granted_by_username = serializers.CharField(source='granted_by.username', read_only=True)

    class Meta:
        model = Mantle
        fields = ['heir_id', 'heir_username', 'granted_by_id', 'granted_by_username', 'end_time', 'is_active']

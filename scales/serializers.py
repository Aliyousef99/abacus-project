from rest_framework import serializers
from .models import Faction, Leverage

class FactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Faction
        fields = ['id', 'name', 'threat_index', 'description']

class LeverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leverage
        fields = ['id', 'description', 'potency', 'acquired_at']
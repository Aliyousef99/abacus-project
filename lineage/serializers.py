from rest_framework import serializers
from .models import Agent

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = ['id', 'alias', 'real_name', 'status', 'loyalty_type', 'key_skill', 'updated_at']
from rest_framework import serializers
from .models import Agent

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        # Ensure all fields from the model are included, especially the new ones.
        fields = [
            'id', 'alias', 'real_name', 'status', 'key_skill', 'loyalty_type',
            'summary', 'picture_url', 'personality', 'locations', 'vehicles',
            'surveillance_images'
        ]
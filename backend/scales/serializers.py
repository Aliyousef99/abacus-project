from rest_framework import serializers
from .models import Faction, Agent, Leverage, Connection
from lineage.models import Agent as LineageAgent

class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = '__all__'

class FactionSerializer(serializers.ModelSerializer):
    members = AgentSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Faction
        fields = [
            'id', 'name', 'threat_index', 'description', 'is_active',
            'picture_url', 'allies', 'strengths', 'weaknesses', 'members', 'member_count'
        ]

    def get_member_count(self, obj):
        """
        Calculates the number of members in the faction.
        """
        return obj.members.count()

class LeverageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leverage
        fields = '__all__'

class ConnectionSerializer(serializers.ModelSerializer):
    scales_agent_id = serializers.IntegerField(source='scales_agent.id', read_only=True)
    scales_agent_alias = serializers.CharField(source='scales_agent.alias', read_only=True)
    lineage_agent_id = serializers.IntegerField(source='lineage_agent.id')
    lineage_agent_alias = serializers.CharField(source='lineage_agent.alias', read_only=True)

    class Meta:
        model = Connection
        fields = ['id', 'scales_agent_id', 'scales_agent_alias', 'lineage_agent_id', 'lineage_agent_alias', 'relationship', 'note', 'created_at']
        read_only_fields = ['id', 'scales_agent_id', 'scales_agent_alias', 'lineage_agent_alias', 'created_at']

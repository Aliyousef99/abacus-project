from rest_framework import serializers
from .models import Operation, OperationLog, Asset, AssetRequisition
from lineage.serializers import AgentSerializer  # Assuming this exists for nesting
from scales.serializers import FactionSerializer # Assuming this exists for nesting
from codex.serializers import CodexEntrySerializer   # Assuming this exists for nesting

class OperationSerializer(serializers.ModelSerializer):
    """Serializer for the list view of operations."""
    class Meta:
        model = Operation
        fields = ['id', 'codename', 'objective', 'status', 'success_probability', 'started_at', 'ended_at']

class OperationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for a single operation profile."""
    targets = FactionSerializer(many=True, read_only=True)
    personnel = AgentSerializer(many=True, read_only=True)
    contingencies = CodexEntrySerializer(many=True, read_only=True)

    class Meta:
        model = Operation
        fields = [
            'id', 'codename', 'objective', 'status', 
            'success_probability', 'collateral_risk',
            'targets', 'personnel', 'contingencies', 'assets', 'after_action_report',
            'created_at', 'updated_at', 'started_at', 'ended_at'
        ]

class OperationLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = OperationLog
        fields = ['id', 'user', 'user_username', 'message', 'timestamp']
        read_only_fields = ['id', 'user', 'user_username', 'timestamp']

class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ['id', 'name', 'type', 'status']

class AssetRequisitionSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)
    asset_type = serializers.CharField(source='asset.type', read_only=True)
    requested_by_username = serializers.CharField(source='requested_by.username', read_only=True)
    approved_by_username = serializers.CharField(source='approved_by.username', read_only=True)
    class Meta:
        model = AssetRequisition
        fields = [
            'id', 'operation', 'asset', 'asset_name', 'asset_type',
            'requested_by', 'requested_by_username', 'status',
            'approved_by', 'approved_by_username', 'decided_at', 'note', 'created_at'
        ]
        read_only_fields = ['requested_by', 'status', 'approved_by', 'decided_at', 'created_at']

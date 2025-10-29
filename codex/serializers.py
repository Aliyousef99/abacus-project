from rest_framework import serializers
from .models import CodexEntry, Echo, Task, SiloComment, VaultItem, PropertyDossier, Vehicle, Bulletin, BulletinAck, Notification

class CodexEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CodexEntry
        fields = ['id', 'title', 'summary', 'content', 'entry_type', 'image_urls', 'created_at']

class EchoSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    decided_by_username = serializers.CharField(source='decided_by.username', read_only=True)
    assigned = serializers.SerializerMethodField()
    class Meta:
        model = Echo
        fields = ['id', 'title', 'content', 'suggested_target', 'confidence', 'involved_entities', 'evidence_urls', 'status', 'created_by', 'created_by_username', 'decided_by', 'decided_by_username', 'created_at', 'decided_at', 'assigned']
        read_only_fields = ['status', 'created_by', 'created_by_username', 'decided_by', 'decided_by_username', 'created_at', 'decided_at']
    def get_assigned(self, obj):
        return [{'id': a.id, 'alias': a.alias} for a in obj.assigned_agents.all()]

class TaskSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'created_by', 'created_by_username', 'assigned_to', 'assigned_to_username', 'created_at', 'related_app', 'related_id']
        read_only_fields = ['created_by', 'created_by_username', 'created_at']

class SiloCommentSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = SiloComment
        fields = ['id', 'echo', 'user', 'user_username', 'message', 'created_at']
        read_only_fields = ['id', 'echo', 'user', 'user_username', 'created_at']

class VaultItemSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    class Meta:
        model = VaultItem
        fields = ['id', 'item_type', 'name', 'identifier', 'notes', 'secret', 'created_by', 'created_by_username', 'created_at']
        read_only_fields = ['created_by', 'created_by_username', 'created_at']

class PropertyDossierSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    stored_items = serializers.PrimaryKeyRelatedField(queryset=VaultItem.objects.all(), many=True, required=False)
    class Meta:
        model = PropertyDossier
        fields = ['id', 'name', 'address', 'photos_urls', 'blueprints_urls', 'security_details', 'vulnerabilities', 'stored_items', 'created_by', 'created_by_username', 'created_at']
        read_only_fields = ['created_by', 'created_by_username', 'created_at']

class VehicleSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    assigned_agent_alias = serializers.CharField(source='assigned_agent.alias', read_only=True)
    class Meta:
        model = Vehicle
        fields = ['id', 'make', 'model', 'year', 'vin', 'license_plate_clean', 'license_plate_cloned', 'modifications', 'last_known_location', 'picture_urls', 'assigned_agent', 'assigned_agent_alias', 'created_by', 'created_by_username', 'created_at']
        read_only_fields = ['created_by', 'created_by_username', 'created_at', 'assigned_agent_alias']

class BulletinSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    acknowledged = serializers.SerializerMethodField()

    class Meta:
        model = Bulletin
        fields = ['id', 'title', 'message', 'audience', 'created_by', 'created_by_username', 'created_at', 'acknowledged']
        read_only_fields = ['created_by', 'created_by_username', 'created_at', 'acknowledged']

    def get_acknowledged(self, obj):
        user = self.context.get('request').user if self.context.get('request') else None
        if not user or not user.is_authenticated:
            return False
        return obj.acks.filter(user=user).exists()

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notif_type', 'message', 'created_at', 'read_at', 'metadata']
        read_only_fields = ['id', 'created_at', 'read_at']

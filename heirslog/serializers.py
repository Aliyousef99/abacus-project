from rest_framework import serializers
from .models import HeirsLogEntry, HeirsLogComment

class HeirsLogCommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)

    class Meta:
        model = HeirsLogComment
        fields = '__all__'
        read_only_fields = ('author', 'entry',)

class HeirsLogEntrySerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    comments = HeirsLogCommentSerializer(many=True, read_only=True)

    class Meta:
        model = HeirsLogEntry
        fields = '__all__'
        read_only_fields = ('author',)
        extra_kwargs = {
            'title': {'required': False, 'allow_blank': True},
            'situational_overview': {'required': False, 'allow_blank': True},
            'critical_intelligence': {'required': False, 'allow_blank': True},
            'operational_status': {'required': False, 'allow_blank': True},
            'strategic_analysis': {'required': False, 'allow_blank': True},
            'proposed_actions': {'required': False, 'allow_blank': True},
            'notes_font_family': {'required': False, 'allow_blank': True},
            'notes_font_size': {'required': False, 'allow_blank': True},
        }

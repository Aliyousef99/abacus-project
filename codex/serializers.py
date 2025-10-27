from rest_framework import serializers
from .models import CodexEntry

class CodexEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = CodexEntry
        fields = ['id', 'title', 'content', 'entry_type', 'created_at']
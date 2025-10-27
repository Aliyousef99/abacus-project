from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import CodexEntry
from .serializers import CodexEntrySerializer

class CodexEntryViewSet(ReadOnlyModelViewSet):
    """
    A read-only endpoint for Codex entries.
    """
    queryset = CodexEntry.objects.all().order_by('-created_at')
    serializer_class = CodexEntrySerializer
    permission_classes = [IsAuthenticated]
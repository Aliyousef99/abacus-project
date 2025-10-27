from rest_framework import viewsets, permissions
from .models import Agent
from .serializers import AgentSerializer
from api.permissions import IsProtector

class AgentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for Lineage Agents.
    GET (List, Retrieve): Open to all authenticated users.
    POST, PUT, PATCH, DELETE: Restricted to 'protector' role.
    """
    queryset = Agent.objects.all().order_by('alias')
    serializer_class = AgentSerializer

    def get_permissions(self):
        """Instantiates and returns the list of permissions that this view requires."""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsProtector]
        return [permission() for permission in permission_classes]
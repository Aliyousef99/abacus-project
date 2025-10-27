from rest_framework import generics, permissions
from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Faction, Leverage
from .serializers import FactionSerializer, LeverageSerializer
from api.permissions import IsProtector

class FactionViewSet(ReadOnlyModelViewSet):
    """
    Read-only endpoint for listing Factions.
    """
    queryset = Faction.objects.all()
    serializer_class = FactionSerializer
    permission_classes = [permissions.IsAuthenticated]

class FactionLeverageView(generics.ListAPIView):
    """
    Endpoint to view leverage on a specific faction.
    Requires 'protector' role.
    """
    serializer_class = LeverageSerializer
    permission_classes = [IsProtector]

    def get_queryset(self):
        faction_id = self.kwargs['id']
        return Leverage.objects.filter(faction_id=faction_id)
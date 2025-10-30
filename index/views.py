from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q

from .models import IndexProfile
from .serializers import IndexProfileSerializer
from api.permissions import get_user_role, IsProtector, IsHQ


class IndexProfileViewSet(viewsets.ModelViewSet):
    queryset = IndexProfile.objects.prefetch_related('affiliations').all().order_by('full_name')
    serializer_class = IndexProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # Read for any authenticated user; write for Protector/HQ; delete HQ only
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['destroy']:
            self.permission_classes = [IsHQ]
        elif self.action in ['create']:
            # Allow all authenticated users to create profiles
            self.permission_classes = [IsAuthenticated]
        else:  # update, partial_update
            # Allow all authenticated users to edit
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        # Text search
        q = self.request.query_params.get('q')
        if q:
            qs = qs.filter(Q(full_name__icontains=q) | Q(aliases__icontains=q) | Q(biography__icontains=q))
        # Filters
        classification = self.request.query_params.get('classification')
        if classification:
            qs = qs.filter(classification=classification)
        affiliation = self.request.query_params.get('affiliation')
        if affiliation:
            try:
                qs = qs.filter(affiliations__id=int(affiliation))
            except ValueError:
                pass
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        threat = self.request.query_params.get('threat_level')
        if threat:
            qs = qs.filter(threat_level=threat)
        return qs

    def perform_create(self, serializer):
        serializer.save()

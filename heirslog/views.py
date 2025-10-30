from rest_framework import viewsets, status
from .models import HeirsLogEntry, HeirsLogComment
from .serializers import HeirsLogEntrySerializer, HeirsLogCommentSerializer
from rest_framework.permissions import IsAuthenticated
from api.permissions import IsHeir, IsProtector, IsOverlooker, IsHQ, get_user_role
from rest_framework.permissions import BasePermission


class IsHeirProtectorOverlookerOrHQ(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) in ['HEIR', 'PROTECTOR', 'OVERLOOKER', 'HQ']

class IsStrictHeir(BasePermission):
    def has_permission(self, request, view):
        return get_user_role(request.user) == 'HEIR'
from rest_framework.decorators import action
from rest_framework.response import Response

class HeirsLogEntryViewSet(viewsets.ModelViewSet):
    queryset = HeirsLogEntry.objects.all().order_by('-entry_date')
    serializer_class = HeirsLogEntrySerializer

    def get_permissions(self):
        # Create and edit allowed to Heir and HQ; delete strictly Heir
        if self.action == 'destroy':
            permission_classes = [IsAuthenticated, IsStrictHeir]
        elif self.action in ['create', 'update', 'partial_update']:
            permission_classes = [IsAuthenticated, IsHeir]
        else:
            # Heir, Protector, Overlooker, HQ can read
            permission_classes = [IsAuthenticated, IsHeirProtectorOverlookerOrHQ]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        entry = self.get_object()
        comments = entry.comments.all().order_by('created_at')
        serializer = HeirsLogCommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsHQ])
    def add_comment(self, request, pk=None):
        entry = self.get_object()
        serializer = HeirsLogCommentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, entry=entry)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

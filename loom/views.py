from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from django.utils import timezone
from .models import Operation, OperationLog, Asset, AssetRequisition
from .serializers import (
    OperationSerializer, OperationDetailSerializer,
    OperationLogSerializer, AssetSerializer, AssetRequisitionSerializer
)
from scales.models import Faction
from lineage.models import Agent
from api.permissions import get_user_role, IsProtector, IsProtectorOrHeir
from audit.utils import log_action

class OperationViewSet(viewsets.ModelViewSet):
    queryset = Operation.objects.all().order_by('-created_at')
    serializer_class = OperationSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OperationDetailSerializer
        return OperationSerializer

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action in ['list', 'retrieve']:
            self.permission_classes = [IsAuthenticated]
        elif self.action in ['create', 'link_target', 'unlink_target', 'assign_personnel', 'unassign_personnel']:
            self.permission_classes = [IsProtectorOrHeir]
        elif self.action == 'commence':
            self.permission_classes = [IsProtector]
        elif self.action in ['conclude', 'abort', 'logs', 'requisitions']:
            self.permission_classes = [IsProtectorOrHeir]
        else: # update, partial_update, destroy
            self.permission_classes = [IsProtectorOrHeir] # Logic inside methods will handle finer details
        return super().get_permissions()

    def perform_create(self, serializer):
        op = serializer.save()
        log_action(self.request.user, f"Created operation '{op.codename}'", target=op)

    def perform_update(self, serializer):
        role = get_user_role(self.request.user)
        operation = self.get_object()

        if role == 'HEIR' and operation.status != 'PLANNING':
            raise PermissionDenied("Heirs can only edit operations in the PLANNING stage.")
        
        updated_op = serializer.save()
        log_action(self.request.user, f"Updated operation '{updated_op.codename}'", target=updated_op)

    def perform_destroy(self, instance):
        # Only Protector or HQ can hard-delete operations
        if get_user_role(self.request.user) not in ['PROTECTOR', 'HQ']:
            raise PermissionDenied("Only the Protector or HQ can delete operations.")
        
        op_name = instance.codename
        log_action(self.request.user, f"Deleted operation '{op_name}'", target=instance)
        instance.delete()

    @action(detail=True, methods=['post'], url_path='link-target')
    def link_target(self, request, pk=None):
        operation = self.get_object()
        if operation.status != 'PLANNING':
            return Response({'error': 'Targets cannot be modified once operation is ACTIVE.'}, status=status.HTTP_400_BAD_REQUEST)
        faction = get_object_or_404(Faction, pk=request.data.get('faction_id'))
        operation.targets.add(faction)
        log_action(request.user, f"Linked target '{faction.name}' to operation '{operation.codename}'", target=operation)
        return Response({'status': 'target linked'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='unlink-target')
    def unlink_target(self, request, pk=None):
        operation = self.get_object()
        if operation.status != 'PLANNING':
            return Response({'error': 'Targets cannot be modified once operation is ACTIVE.'}, status=status.HTTP_400_BAD_REQUEST)
        faction = get_object_or_404(Faction, pk=request.data.get('faction_id'))
        operation.targets.remove(faction)
        log_action(request.user, f"Unlinked target '{faction.name}' from operation '{operation.codename}'", target=operation)
        return Response({'status': 'target unlinked'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='assign-personnel')
    def assign_personnel(self, request, pk=None):
        operation = self.get_object()
        if operation.status != 'PLANNING':
            return Response({'error': 'Personnel cannot be modified once operation is ACTIVE.'}, status=status.HTTP_400_BAD_REQUEST)
        agent = get_object_or_404(Agent, pk=request.data.get('agent_id'))
        operation.personnel.add(agent)
        log_action(request.user, f"Assigned agent '{agent.alias}' to operation '{operation.codename}'", target=operation)
        return Response({'status': 'personnel assigned'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='unassign-personnel')
    def unassign_personnel(self, request, pk=None):
        operation = self.get_object()
        if operation.status != 'PLANNING':
            return Response({'error': 'Personnel cannot be modified once operation is ACTIVE.'}, status=status.HTTP_400_BAD_REQUEST)
        agent = get_object_or_404(Agent, pk=request.data.get('agent_id'))
        operation.personnel.remove(agent)
        log_action(request.user, f"Unassigned agent '{agent.alias}' from operation '{operation.codename}'", target=operation)
        return Response({'status': 'personnel unassigned'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='commence')
    def commence(self, request, pk=None):
        """Protector-only action to begin an operation."""
        operation = self.get_object()
        if operation.status != 'PLANNING':
            return Response({'error': 'Operation is not in the PLANNING stage.'}, status=status.HTTP_400_BAD_REQUEST)
        
        operation.status = 'ACTIVE'
        operation.started_at = timezone.now()
        operation.save()
        log_action(request.user, f"Commenced operation '{operation.codename}'", target=operation)
        # Notify leadership about operation status change
        try:
            from django.contrib.auth.models import User as DjangoUser
            from codex.models import Notification
            recipients = DjangoUser.objects.filter(profile__role__in=['PROTECTOR', 'HEIR']).distinct()
            Notification.objects.bulk_create([
                Notification(
                    user=u,
                    notif_type=Notification.Type.OPERATION_STATUS,
                    message=f"Operation '{operation.codename}' commenced",
                    metadata={'operation_id': operation.id, 'status': operation.status}
                ) for u in recipients
            ])
        except Exception:
            pass
        return Response(self.get_serializer(operation).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='conclude')
    def conclude(self, request, pk=None):
        operation = self.get_object()
        if operation.status != 'ACTIVE':
            return Response({'error': 'Only ACTIVE operations can be concluded.'}, status=status.HTTP_400_BAD_REQUEST)
        outcome = request.data.get('outcome')  # 'SUCCESS' or 'FAILURE'
        report = request.data.get('report', '')
        if outcome not in ['SUCCESS', 'FAILURE']:
            return Response({'error': 'Invalid outcome. Use SUCCESS or FAILURE.'}, status=status.HTTP_400_BAD_REQUEST)
        operation.status = 'CONCLUDED - SUCCESS' if outcome == 'SUCCESS' else 'CONCLUDED - FAILURE'
        operation.after_action_report = report
        operation.ended_at = timezone.now()
        operation.save()
        # Release allocated assets for this operation
        approved = AssetRequisition.objects.filter(operation=operation, status='APPROVED').select_related('asset')
        for req in approved:
            req.asset.status = 'AVAILABLE'
            req.asset.save(update_fields=['status'])
        log_action(request.user, f"Concluded operation '{operation.codename}' ({outcome})", target=operation)
        try:
            from django.contrib.auth.models import User as DjangoUser
            from codex.models import Notification
            recipients = DjangoUser.objects.filter(profile__role__in=['PROTECTOR', 'HEIR']).distinct()
            Notification.objects.bulk_create([
                Notification(
                    user=u,
                    notif_type=Notification.Type.OPERATION_STATUS,
                    message=f"Operation '{operation.codename}' concluded: {outcome}",
                    metadata={'operation_id': operation.id, 'status': operation.status}
                ) for u in recipients
            ])
        except Exception:
            pass
        return Response(self.get_serializer(operation).data)

    @action(detail=True, methods=['post'], url_path='abort')
    def abort(self, request, pk=None):
        operation = self.get_object()
        if operation.status != 'ACTIVE':
            return Response({'error': 'Only ACTIVE operations can be aborted.'}, status=status.HTTP_400_BAD_REQUEST)
        reason = request.data.get('reason', '')
        operation.status = 'COMPROMISED'
        operation.after_action_report = (operation.after_action_report or '') + (f"\nABORTED: {reason}" if reason else '')
        operation.ended_at = timezone.now()
        operation.save()
        approved = AssetRequisition.objects.filter(operation=operation, status='APPROVED').select_related('asset')
        for req in approved:
            req.asset.status = 'AVAILABLE'
            req.asset.save(update_fields=['status'])
        log_action(request.user, f"Aborted operation '{operation.codename}'", target=operation)
        try:
            from django.contrib.auth.models import User as DjangoUser
            from codex.models import Notification
            recipients = DjangoUser.objects.filter(profile__role__in=['PROTECTOR', 'HEIR']).distinct()
            Notification.objects.bulk_create([
                Notification(
                    user=u,
                    notif_type=Notification.Type.OPERATION_STATUS,
                    message=f"Operation '{operation.codename}' aborted",
                    metadata={'operation_id': operation.id, 'status': operation.status}
                ) for u in recipients
            ])
        except Exception:
            pass
        return Response(self.get_serializer(operation).data)

    @action(detail=True, methods=['get', 'post'], url_path='logs')
    def logs(self, request, pk=None):
        operation = self.get_object()
        if request.method.lower() == 'get':
            qs = operation.logs.all()
            return Response(OperationLogSerializer(qs, many=True).data)
        # POST: add log entry
        if operation.status != 'ACTIVE':
            return Response({'error': 'Logs can only be added while operation is ACTIVE.'}, status=status.HTTP_400_BAD_REQUEST)
        message = request.data.get('message')
        if not message:
            return Response({'error': 'message is required'}, status=status.HTTP_400_BAD_REQUEST)
        log = OperationLog.objects.create(operation=operation, user=request.user, message=message)
        log_action(request.user, f"Log entry added to '{operation.codename}'", target=operation)
        return Response(OperationLogSerializer(log).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='requisitions')
    def requisitions(self, request, pk=None):
        operation = self.get_object()
        if request.method.lower() == 'get':
            qs = operation.requisitions.select_related('asset', 'requested_by', 'approved_by').order_by('-created_at')
            return Response(AssetRequisitionSerializer(qs, many=True).data)
        # POST create requisition
        asset_id = request.data.get('asset_id')
        if not asset_id:
            return Response({'error': 'asset_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        asset = get_object_or_404(Asset, pk=asset_id)
        if asset.status != 'AVAILABLE':
            return Response({'error': 'Asset is not available'}, status=status.HTTP_400_BAD_REQUEST)
        req, created = AssetRequisition.objects.get_or_create(
            operation=operation, asset=asset,
            defaults={'requested_by': request.user, 'status': 'PENDING'}
        )
        if not created:
            return Response({'error': 'Requisition already exists for this asset.'}, status=status.HTTP_400_BAD_REQUEST)
        log_action(request.user, f"Requested asset '{asset.name}' for operation '{operation.codename}'", target=operation)
        return Response(AssetRequisitionSerializer(req).data, status=status.HTTP_201_CREATED)

class AssetViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Asset.objects.all().order_by('name')
    serializer_class = AssetSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

class AssetRequisitionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AssetRequisition.objects.select_related('asset', 'operation', 'requested_by', 'approved_by').all()
    serializer_class = AssetRequisitionSerializer
    permission_classes = [IsProtector]

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        req = self.get_object()
        if req.status != 'PENDING':
            return Response({'error': 'Requisition is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        req.status = 'APPROVED'
        req.approved_by = request.user
        req.decided_at = timezone.now()
        req.save(update_fields=['status', 'approved_by', 'decided_at'])
        req.asset.status = 'ALLOCATED'
        req.asset.save(update_fields=['status'])
        log_action(request.user, f"Approved asset '{req.asset.name}' for operation '{req.operation.codename}'", target=req.operation)
        return Response(AssetRequisitionSerializer(req).data)

    @action(detail=True, methods=['post'], url_path='deny')
    def deny(self, request, pk=None):
        req = self.get_object()
        if req.status != 'PENDING':
            return Response({'error': 'Requisition is not pending.'}, status=status.HTTP_400_BAD_REQUEST)
        req.status = 'DENIED'
        req.approved_by = request.user
        req.decided_at = timezone.now()
        req.save(update_fields=['status', 'approved_by', 'decided_at'])
        log_action(request.user, f"Denied asset '{req.asset.name}' for operation '{req.operation.codename}'", target=req.operation)
        return Response(AssetRequisitionSerializer(req).data)

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Faction, Agent, Connection, FactionHistory
from audit.models import AuditLog
from .serializers import FactionSerializer, AgentSerializer, ConnectionSerializer
from api.permissions import get_user_role, IsProtectorOrHeir
from audit.utils import log_action

class FactionViewSet(viewsets.ModelViewSet):
    """
    Provides CRUD for Factions with role-based permissions.
    """
    serializer_class = FactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        role = get_user_role(self.request.user)
        if role in ['PROTECTOR', 'HQ']:
            return Faction.all_objects.prefetch_related('members').all().order_by('name')
        return Faction.objects.prefetch_related('members').all().order_by('name')

    def perform_create(self, serializer):
        faction = serializer.save()
        log_action(self.request.user, f"Created faction '{faction.name}'", target=faction)

    def perform_update(self, serializer):
        # Capture previous values for change detection
        prev = serializer.instance
        prev_threat = prev.threat_index
        prev_members = prev.member_count if hasattr(prev, 'member_count') else None
        faction = serializer.save()
        log_action(self.request.user, f"Updated faction '{faction.name}'", target=faction)
        # Log history if key indicators changed
        if faction.threat_index != prev_threat:
            FactionHistory.objects.create(
                faction=faction,
                threat_index=faction.threat_index,
                member_count=faction.member_count,
                updated_by=self.request.user,
            )

    def perform_destroy(self, instance):
        role = get_user_role(self.request.user)
        faction_name = instance.name

        if role in ['PROTECTOR', 'HQ']:
            log_action(self.request.user, f"Permanently deleted faction '{faction_name}'", target=instance)
            instance.delete()  # Hard delete
        elif role == 'HEIR':
            instance.deleted_at = timezone.now()
            instance.save()
            log_action(self.request.user, f"Archived faction '{faction_name}'", target=instance)
        else:  # Overlooker and any other role
            log_action(self.request.user, f"Denied attempt to delete faction '{faction_name}'", target=instance)
            raise PermissionDenied("You do not have permission to delete factions.")

    @action(detail=True, methods=['post'], url_path='members', permission_classes=[IsProtectorOrHeir])
    def add_member(self, request, pk=None):
        faction = self.get_object()
        agent_id = request.data.get('agent_id')
        try:
            agent = Agent.objects.get(id=agent_id)
            faction.members.add(agent)
            log_action(request.user, f"Added member '{agent.alias}' to faction '{faction.name}'", target=faction)
            # Log history snapshot for member count change
            FactionHistory.objects.create(
                faction=faction,
                threat_index=faction.threat_index,
                member_count=faction.member_count,
                updated_by=request.user,
            )
            return Response({'status': 'member added'}, status=status.HTTP_200_OK)
        except Agent.DoesNotExist:
            return Response({'error': 'Agent not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'], url_path='history', permission_classes=[IsAuthenticated])
    def history(self, request, pk=None):
        faction = self.get_object()
        qs = FactionHistory.objects.filter(faction=faction).order_by('timestamp')
        data = [
            {
                'timestamp': h.timestamp,
                'threat_index': h.threat_index,
                'member_count': h.member_count,
            }
            for h in qs
        ]
        return Response(data)

    @action(detail=False, methods=['get'], url_path='network', permission_classes=[IsAuthenticated])
    def network(self, request):
        """Return a simple node-link graph of factions, their members, and lineage connections."""
        factions = list(Faction.objects.prefetch_related('members').all())
        scales_agents = list(Agent.objects.all())
        conns = list(Connection.objects.select_related('scales_agent', 'lineage_agent').all())

        nodes = []
        links = []
        seen = set()

        for f in factions:
            nid = f"F-{f.id}"
            if nid not in seen:
                nodes.append({ 'id': nid, 'type': 'FACTION', 'label': f.name, 'threat': f.threat_index })
                seen.add(nid)
            for m in f.members.all():
                sid = f"S-{m.id}"
                if sid not in seen:
                    nodes.append({ 'id': sid, 'type': 'SCALES_AGENT', 'label': m.alias })
                    seen.add(sid)
                links.append({ 'source': sid, 'target': nid, 'kind': 'MEMBER_OF' })

        for c in conns:
            sid = f"S-{c.scales_agent_id}"
            lid = f"L-{c.lineage_agent_id}"
            if sid not in seen:
                nodes.append({ 'id': sid, 'type': 'SCALES_AGENT', 'label': c.scales_agent.alias })
                seen.add(sid)
            if lid not in seen:
                nodes.append({ 'id': lid, 'type': 'LINEAGE_AGENT', 'label': c.lineage_agent.alias })
                seen.add(lid)
            links.append({ 'source': sid, 'target': lid, 'kind': 'CONNECTION', 'relationship': c.relationship })

        return Response({ 'nodes': nodes, 'links': links })

    @action(detail=True, methods=['get'], url_path='timeline', permission_classes=[IsAuthenticated])
    def timeline(self, request, pk=None):
        """Aggregate faction timeline: history snapshots + audit references."""
        faction = self.get_object()
        items = []
        # Faction history points
        for h in FactionHistory.objects.filter(faction=faction).order_by('-timestamp'):
            items.append({
                'timestamp': h.timestamp,
                'source': 'HISTORY',
                'type': 'FACTION_METRICS',
                'text': f"Threat {h.threat_index}, Members {h.member_count}",
            })
        # Audit logs linked to this faction
        for log in AuditLog.objects.filter(content_type__model='faction', object_id=faction.id).order_by('-timestamp')[:200]:
            items.append({ 'timestamp': log.timestamp, 'source': 'AUDIT', 'type': 'ACTION', 'text': log.action })
        items.sort(key=lambda x: x['timestamp'], reverse=True)
        return Response(items)

class AgentViewSet(viewsets.ModelViewSet):
    """
    Provides CRUD for external agents (faction members) with role-based permissions.
    """
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        role = get_user_role(self.request.user)
        if role in ['PROTECTOR', 'HQ']:
            return Agent.all_objects.all().order_by('alias')
        return Agent.objects.all().order_by('alias')

    def perform_create(self, serializer):
        agent = serializer.save()
        log_action(self.request.user, f"Created external agent '{agent.alias}'", target=agent)

    def perform_update(self, serializer):
        agent = serializer.save()
        log_action(self.request.user, f"Updated external agent '{agent.alias}'", target=agent)

    def perform_destroy(self, instance):
        role = get_user_role(self.request.user)
        agent_alias = instance.alias

        if role in ['PROTECTOR', 'HQ']:
            log_action(self.request.user, f"Permanently deleted external agent '{agent_alias}'", target=instance)
            instance.delete()
        elif role == 'HEIR':
            instance.deleted_at = timezone.now()
            instance.save()
            log_action(self.request.user, f"Archived external agent '{agent_alias}'", target=instance)
        else:
            log_action(self.request.user, f"Denied attempt to delete external agent '{agent_alias}'", target=instance)
            raise PermissionDenied("You do not have permission to delete these agents.")

    @action(detail=True, methods=['get', 'post'], url_path='connections', permission_classes=[IsAuthenticated])
    def connections(self, request, pk=None):
        """List or create connections for a Scales agent to a Lineage agent.
        GET: list connections for this Scales agent.
        POST: create connection; requires IsProtectorOrHeir role.
        Body: { lineage_agent_id: int, relationship: str, note?: str }
        """
        scales_agent = self.get_object()
        if request.method.lower() == 'get':
            qs = Connection.objects.filter(scales_agent=scales_agent).select_related('lineage_agent')
            return Response(ConnectionSerializer(qs, many=True).data)

        # POST create
        role = get_user_role(request.user)
        if role not in ['PROTECTOR', 'HEIR', 'HQ']:
            raise PermissionDenied("You do not have permission to create connections.")
        lineage_agent_id = request.data.get('lineage_agent_id')
        relationship = request.data.get('relationship')
        note = request.data.get('note', '')
        if not lineage_agent_id or not relationship:
            return Response({'error': 'lineage_agent_id and relationship are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            lineage_agent = __import__('lineage.models', fromlist=['Agent']).Agent.objects.get(pk=lineage_agent_id)
        except Exception:
            return Response({'error': 'Lineage agent not found.'}, status=status.HTTP_404_NOT_FOUND)
        if relationship not in dict(Connection.Relationship.choices):
            return Response({'error': 'Invalid relationship value.'}, status=status.HTTP_400_BAD_REQUEST)
        conn, created = Connection.objects.get_or_create(
            scales_agent=scales_agent,
            lineage_agent=lineage_agent,
            defaults={'relationship': relationship, 'note': note}
        )
        if not created:
            # Update relationship/note if already exists
            conn.relationship = relationship
            conn.note = note
            conn.save(update_fields=['relationship', 'note'])
        log_action(request.user, f"Linked scales agent '{scales_agent.alias}' to lineage agent '{lineage_agent.alias}' as {relationship}", target=scales_agent)
        return Response(ConnectionSerializer(conn).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
        # DELETE unlink (body should contain lineage_agent_id)
        
    @connections.mapping.delete
    def delete_connection(self, request, pk=None):
        scales_agent = self.get_object()
        role = get_user_role(request.user)
        if role not in ['PROTECTOR', 'HEIR', 'HQ']:
            raise PermissionDenied("You do not have permission to remove connections.")
        lineage_agent_id = request.data.get('lineage_agent_id')
        if not lineage_agent_id:
            return Response({'error': 'lineage_agent_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            conn = Connection.objects.get(scales_agent=scales_agent, lineage_agent_id=lineage_agent_id)
        except Connection.DoesNotExist:
            return Response({'error': 'Connection not found.'}, status=status.HTTP_404_NOT_FOUND)
        alias = conn.lineage_agent.alias
        conn.delete()
        log_action(request.user, f"Unlinked scales agent '{scales_agent.alias}' from lineage agent '{alias}'", target=scales_agent)
        return Response(status=status.HTTP_204_NO_CONTENT)

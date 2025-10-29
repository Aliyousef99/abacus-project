from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import UserProfile, Mantle, SiteState, PanicAlert
from django.db import transaction, IntegrityError, DatabaseError
from .serializers import UserProfileSerializer
from api.permissions import IsProtector, IsTrueProtector
from api.permissions import get_user_role
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Expose base role only (do not elevate via mantle here)
        role = getattr(getattr(self.user, 'profile', None), 'role', None)
        data['role'] = role
        data['username'] = self.user.username
        data['user_id'] = self.user.id
        return data


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing users and managing Protector's Mantle.
    """
    queryset = UserProfile.objects.select_related('user').all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsTrueProtector] # Only true Protector can access this viewset

    @action(detail=False, methods=['post'], url_path='grant-mantle', permission_classes=[IsTrueProtector])
    def grant_mantle(self, request):
        heir_id = request.data.get('heir_id')
        duration_hours = request.data.get('duration_hours')

        if heir_id in (None, "") or duration_hours in (None, ""):
            return Response({'error': 'Heir ID and duration are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            duration_hours = int(duration_hours)
        except (TypeError, ValueError):
            return Response({'error': 'Duration must be an integer number of hours.'}, status=status.HTTP_400_BAD_REQUEST)

        if duration_hours <= 0:
            return Response({'error': 'Duration must be greater than zero hours.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            heir_user = User.objects.get(pk=heir_id, profile__role='HEIR')
        except User.DoesNotExist:
            return Response({'error': 'Heir not found or not an HEIR.'}, status=status.HTTP_404_NOT_FOUND)

        end_time = timezone.now() + timedelta(hours=duration_hours)

        try:
            with transaction.atomic():
                # Ensure only one Mantle per user (OneToOne). If it exists, update it; otherwise create it.
                mantle, created = Mantle.objects.update_or_create(
                    user=heir_user,
                    defaults={
                        'granted_by': request.user,
                        'end_time': end_time,
                        'is_active': True,
                    }
                )
        except IntegrityError:
            return Response({'error': 'Failed to grant mantle due to a data integrity error.'}, status=status.HTTP_400_BAD_REQUEST)
        except DatabaseError as e:
            return Response({'error': f'Database error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': f'Unexpected error: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Notify heir of mantle grant
        try:
            from codex.models import Notification
            Notification.objects.create(
                user=heir_user,
                notif_type=Notification.Type.MANTLE,
                message="Protector's Mantle granted",
                metadata={'heir_id': heir_user.id, 'end_time': end_time.isoformat(), 'action': 'granted'}
            )
        except Exception:
            pass
        return Response({'status': f"Mantle granted to {heir_user.username} until {end_time.isoformat()}"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='mantle-status')
    def mantle_status(self, request):
        try:
            mantle = request.user.mantle
            if mantle.is_currently_active():
                return Response({'is_active': True, 'end_time': mantle.end_time})
        except Mantle.DoesNotExist:
            pass
        return Response({'is_active': False})

    # --- Panic and Shutdown Controls ---
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='panic')
    def panic(self, request):
        """Heir/Overlooker submit a panic message; Protector/HQ trigger immediate shutdown."""
        role = get_user_role(request.user)
        message = request.data.get('message', '')
        # Record the alert
        alert = PanicAlert.objects.create(user=request.user, message=message)
        # Notify leadership
        try:
            from codex.models import Notification
            from django.contrib.auth.models import User as DjangoUser
            recipients = DjangoUser.objects.filter(profile__role__in=['PROTECTOR', 'HQ']).distinct()
            Notification.objects.bulk_create([
                Notification(user=u, notif_type='MANTLE', message=f"{role or 'User'} initiated a panic alert", metadata={'alert_id': alert.id, 'message': message})
                for u in recipients
            ])
        except Exception:
            pass
        # If Protector/HQ, immediately shutdown
        if role in ['PROTECTOR', 'HQ']:
            state = SiteState.get_state()
            state.is_shutdown = True
            state.save(update_fields=['is_shutdown'])
            # Resolve all outstanding alerts so they don't show again
            from django.utils import timezone as djtz
            open_alerts = PanicAlert.objects.filter(resolved_at__isnull=True)
            for a in open_alerts:
                a.resolved_at = djtz.now()
                a.resolved_by = request.user
                a.save(update_fields=['resolved_at', 'resolved_by'])
        return Response({'status': 'ok', 'shutdown': role in ['PROTECTOR', 'HQ']})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='panic-alerts')
    def panic_alerts(self, request):
        role = get_user_role(request.user)
        if role not in ['PROTECTOR', 'HQ']:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        qs = PanicAlert.objects.filter(resolved_at__isnull=True).order_by('-created_at')
        data = [
            {
                'id': a.id,
                'user_username': getattr(a.user, 'username', None),
                'message': a.message,
                'created_at': a.created_at,
            } for a in qs
        ]
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='resolve-panic')
    def resolve_panic(self, request):
        role = get_user_role(request.user)
        if role not in ['PROTECTOR', 'HQ']:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        alert_id = request.data.get('alert_id')
        try:
            alert = PanicAlert.objects.get(pk=alert_id)
        except PanicAlert.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        if alert.resolved_at:
            return Response({'status': 'already resolved'})
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.save(update_fields=['resolved_at', 'resolved_by'])
        return Response({'status': 'resolved'})

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated], url_path='site-status')
    def site_status(self, request):
        st = SiteState.get_state()
        return Response({'shutdown': st.is_shutdown, 'updated_at': st.updated_at})

    @action(detail=False, methods=['post'], permission_classes=[IsProtector], url_path='shutdown')
    def shutdown(self, request):
        """Protector or HQ can initiate shutdown. (IsProtector allows HQ via permission adjustment.)"""
        st = SiteState.get_state()
        st.is_shutdown = True
        st.save(update_fields=['is_shutdown'])
        # Resolve all outstanding alerts so they don't show again
        from django.utils import timezone as djtz
        open_alerts = PanicAlert.objects.filter(resolved_at__isnull=True)
        for a in open_alerts:
            a.resolved_at = djtz.now()
            a.resolved_by = request.user
            a.save(update_fields=['resolved_at', 'resolved_by'])
        return Response({'status': 'shutdown'})

    @action(detail=False, methods=['post'], permission_classes=[IsTrueProtector], url_path='bring-online')
    def bring_online(self, request):
        """Only HQ may bring the site back online (IsTrueProtector includes HQ per our change)."""
        # Enforce HQ explicitly to avoid Protector bringing back
        try:
            if getattr(request.user.profile, 'role', None) != 'HQ':
                return Response({'error': 'Only HQ may bring the site back online.'}, status=status.HTTP_403_FORBIDDEN)
        except Exception:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        st = SiteState.get_state()
        st.is_shutdown = False
        st.save(update_fields=['is_shutdown'])
        return Response({'status': 'online'})

    @action(detail=False, methods=['get'], permission_classes=[IsTrueProtector], url_path='mantles')
    def list_mantles(self, request):
        """List all active mantles with heir and expiration info."""
        mantles = Mantle.objects.select_related('user', 'granted_by').filter(is_active=True).order_by('end_time')
        data = [
            {
                'heir_id': m.user.id,
                'heir_username': m.user.username,
                'granted_by_id': m.granted_by.id if m.granted_by else None,
                'granted_by_username': m.granted_by.username if m.granted_by else None,
                'end_time': m.end_time,
                'is_active': m.is_active,
            }
            for m in mantles
        ]
        return Response(data)

    @action(detail=False, methods=['post'], permission_classes=[IsTrueProtector], url_path='revoke-mantle')
    def revoke_mantle(self, request):
        """Revoke a mantle for a given heir."""
        heir_id = request.data.get('heir_id')
        if not heir_id:
            return Response({'error': 'heir_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            heir_user = User.objects.get(pk=heir_id)
        except User.DoesNotExist:
            return Response({'error': 'Heir not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            mantle = Mantle.objects.get(user=heir_user)
        except Mantle.DoesNotExist:
            return Response({'error': 'Mantle not found for this heir.'}, status=status.HTTP_404_NOT_FOUND)
        mantle.is_active = False
        mantle.end_time = timezone.now()
        mantle.save(update_fields=['is_active', 'end_time'])
        # Notify heir of revocation
        try:
            from codex.models import Notification
            Notification.objects.create(
                user=heir_user,
                notif_type=Notification.Type.MANTLE,
                message="Protector's Mantle revoked",
                metadata={'heir_id': heir_user.id, 'action': 'revoked'}
            )
        except Exception:
            pass
        return Response({'status': f"Mantle revoked for {heir_user.username}."})

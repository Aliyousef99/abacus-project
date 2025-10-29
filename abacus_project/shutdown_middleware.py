from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

EXEMPT_PATHS = (
    '/api/auth/token/',
    '/api/auth/token/refresh/',
    '/api/users/site-status/',
)


class ShutdownMiddleware(MiddlewareMixin):
    """Blocks API access for non-HQ users while site is in shutdown state.

    Allows authentication endpoints and site-status so the frontend can discover
    shutdown and HQ can still log in.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        path = request.path
        # Only enforce for API routes
        if not path.startswith('/api/'):
            return None
        # Permit exempt endpoints
        if any(path.startswith(p) for p in EXEMPT_PATHS):
            return None

        # Lazy import to avoid circular import at startup
        try:
            from users.models import SiteState
            from api.permissions import get_user_role
        except Exception:
            return None

        try:
            if SiteState.get_state().is_shutdown:
                # Determine role; JWT may not be applied yet at middleware layer
                role = None
                try:
                    role = get_user_role(getattr(request, 'user', None))
                except Exception:
                    role = None
                if role != 'HQ':
                    # Attempt JWT auth to resolve user early
                    try:
                        from rest_framework_simplejwt.authentication import JWTAuthentication
                        authenticator = JWTAuthentication()
                        header = request.META.get('HTTP_AUTHORIZATION', '')
                        if header:
                            # Mimic DRF flow
                            raw = header.split(' ', 1)[1] if ' ' in header else header
                            validated = authenticator.get_validated_token(raw)
                            user = authenticator.get_user(validated)
                            role = get_user_role(user)
                    except Exception:
                        pass
                if role != 'HQ':
                    return JsonResponse({'error': 'Site shutdown active. Only HQ may access.'}, status=503)
        except Exception:
            # Fail-open if state cannot be read
            return None
        return None

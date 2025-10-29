from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from api.permissions import IsProtector
from django.contrib.auth.models import User
from users.models import UserProfile

@api_view(['GET'])
@permission_classes([IsProtector])
def administration_panel(request):
    heirs = User.objects.filter(profile__role='HEIR')
    return render(request, 'administration/panel.html', {'heirs': heirs})

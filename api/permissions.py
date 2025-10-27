from rest_framework.permissions import BasePermission

def is_in_group(user, group_name):
    """
    Takes a user and a group name, and returns `True` if the user is in that group.
    """
    return user.groups.filter(name=group_name).exists()

class IsProtector(BasePermission):
    """
    Allows access only to users in the 'protector' group.
    """
    def has_permission(self, request, view):
        return is_in_group(request.user, 'protector')

class IsHeir(BasePermission):
    """
    Allows access only to users in the 'heir' group.
    """
    def has_permission(self, request, view):
        return is_in_group(request.user, 'heir')
from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """
    Allows access only to users with role='admin'.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allows access to the owner of the object, or admins.
    Requires the model to have a `user` attribute, or the view to provide appropriate object.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
            
        if request.user.role == 'admin':
            return True
            
        # Objects can have a 'user' attribute directly or nested (e.g., attempt.user)
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        return False

from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
        Read access for anyone authenticated.
        Write access only for the object's owner or an admin
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if request.user.role == 'admin' or request.user.is_staff:
            return True

        return obj.owner == request.user
       
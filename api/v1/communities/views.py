from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .serializers import CommunitySerializer, JoinCommunitySerializer
from apps.communities.models import Community

class CommunityViewSet(viewsets.ModelViewSet):
    serializer_class = CommunitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return communities the user is a member of
        return Community.objects.filter(members=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        community = serializer.save(creator=self.request.user)
        community.members.add(self.request.user)

    @action(detail=False, methods=['post'], url_path='join')
    def join(self, request):
        serializer = JoinCommunitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        join_code = serializer.validated_data['join_code'].upper()
        community = get_object_or_404(Community, join_code=join_code)
        
        if community.members.filter(id=request.user.id).exists():
            return Response({"detail": "Already a member of this community."}, status=status.HTTP_400_BAD_REQUEST)
            
        community.members.add(request.user)
        return Response(CommunitySerializer(community, context={'request': request}).data, status=status.HTTP_200_OK)

from rest_framework import serializers
from apps.communities.models import Community

class CommunitySerializer(serializers.ModelSerializer):
    creator_name = serializers.ReadOnlyField(source='creator.username')
    is_member = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Community
        fields = ['id', 'name', 'description', 'join_code', 'creator_name', 'is_member', 'member_count', 'created_at']
        read_only_fields = ['id', 'join_code', 'creator_name', 'created_at']

    def get_is_member(self, obj):
        user = self.context.get('request').user if 'request' in self.context else None
        if user:
            return obj.members.filter(id=user.id).exists()
        return False

    def get_member_count(self, obj):
        return obj.members.count()

class JoinCommunitySerializer(serializers.Serializer):
    join_code = serializers.CharField(max_length=12, required=True)

from rest_framework import serializers
from .models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()


class ChatResponseSerializer(serializers.Serializer):
    assistant_message = serializers.CharField()
    properties = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )


class SemanticSearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField()


class SemanticSearchResponseSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()
    title = serializers.CharField()
    description = serializers.CharField()
    similarity_score = serializers.FloatField()


class ExplainRequestSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()
    user_preferences = serializers.CharField(required=False)


class CompareRequestSerializer(serializers.Serializer):
    property_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=2,
        max_length=3
    )

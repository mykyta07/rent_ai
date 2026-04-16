from rest_framework import serializers
from .models import ChatMessage, PropertyExplainChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'role', 'content', 'properties', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatHistoryMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'properties', 'created_at']
        read_only_fields = ['id', 'role', 'content', 'properties', 'created_at']


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()


class ChatResponseSerializer(serializers.Serializer):
    assistant_message = serializers.CharField()
    properties = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )


class PropertyExplainChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()


class PropertyExplainChatResponseSerializer(serializers.Serializer):
    assistant_message = serializers.CharField()


class PropertyExplainChatHistoryMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyExplainChatMessage
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "role", "content", "created_at"]


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


class ExplainBriefRequestSerializer(serializers.Serializer):
    property_id = serializers.IntegerField()


class CompareRequestSerializer(serializers.Serializer):
    property_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=2,
        max_length=3
    )


class ListingDescriptionGenerateSerializer(serializers.Serializer):
    """Контекст з форми додавання оголошення для генерації опису."""

    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    hints = serializers.CharField(required=False, allow_blank=True, max_length=800)
    price = serializers.IntegerField(required=False, min_value=0, default=0)
    currency = serializers.CharField(required=False, allow_blank=True, default="$", max_length=10)
    rooms_count = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    total_area = serializers.FloatField(required=False, allow_null=True)
    living_area = serializers.FloatField(required=False, allow_null=True)
    kitchen_area = serializers.FloatField(required=False, allow_null=True)
    floor = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    floors_count = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    building_type = serializers.CharField(required=False, allow_blank=True, max_length=50)
    is_commercial = serializers.BooleanField(required=False, default=False)
    realty_type = serializers.ChoiceField(
        choices=["apartment", "house", "commercial"],
        required=False,
        default="apartment",
    )
    sale_type = serializers.ChoiceField(choices=["sale", "rent"], required=False, default="sale")
    city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    district = serializers.CharField(required=False, allow_blank=True, max_length=100)
    street = serializers.CharField(required=False, allow_blank=True, max_length=150)
    building_number = serializers.CharField(required=False, allow_blank=True, max_length=20)
    metro_station = serializers.CharField(required=False, allow_blank=True, max_length=120)
    metro_distance_minutes = serializers.IntegerField(required=False, allow_null=True, min_value=0)

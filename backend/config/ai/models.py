from django.db import models
from properties.models import Property
from users.models import User

# Create your models here.
class PropertyEmbedding(models.Model):
    property = models.OneToOneField(
        Property,
        on_delete=models.CASCADE,
        related_name="embedding"
    )

    embedding = models.JSONField(
        help_text="Векторне представлення опису об'єкта"
    )

    model_name = models.CharField(
        max_length=100,
        help_text="Назва моделі (Gemini, sentence-transformer)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "Користувач"),
        ("assistant", "Асистент"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    properties = models.JSONField(
        default=list,
        blank=True,
        help_text="Список ID об'єктів нерухомості, які асистент рекомендував у цьому повідомленні.",
    )
    created_at = models.DateTimeField(auto_now_add=True)


class PropertyExplainChatMessage(models.Model):
    """
    Історія «AI пояснення» для конкретного об'єкта.
    Окремо для кожного користувача і кожного Property.
    """

    ROLE_CHOICES = [
        ("user", "Користувач"),
        ("assistant", "Асистент"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="property_explain_messages",
    )
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="explain_chat_messages",
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

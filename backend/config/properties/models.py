from django.db import models
from django.conf import settings

# Create your models here.
class Property(models.Model):
    SALE_TYPE_CHOICES = [
        ("sale", "Продаж"),
        ("rent", "Оренда"),
    ]

    REALTY_TYPE_CHOICES = [
        ("apartment", "Квартира"),
        ("house", "Будинок"),
        ("commercial", "Комерційна нерухомість"),
    ]

    title = models.CharField(
        max_length=255,
        help_text="Назва оголошення"
    )

    description = models.TextField(
        help_text="Опис об'єкта (для LLM та embeddings)"
    )

    price = models.PositiveIntegerField()
    currency = models.CharField(max_length=10, default="$")

    rooms_count = models.PositiveSmallIntegerField(null=True)
    total_area = models.FloatField(null=True)
    living_area = models.FloatField(null=True)
    kitchen_area = models.FloatField(null=True)

    floor = models.PositiveSmallIntegerField(null=True)
    floors_count = models.PositiveSmallIntegerField(null=True)

    building_type = models.CharField(
        max_length=50,
        null=True,
        help_text="Тип будинку (цегла, панель тощо)"
    )

    is_commercial = models.BooleanField(default=False)
    realty_type = models.CharField(
        max_length=20,
        choices=REALTY_TYPE_CHOICES
    )
    sale_type = models.CharField(
        max_length=10,
        choices=SALE_TYPE_CHOICES
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="properties",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} — {self.price}{self.currency}"



class Location(models.Model):
    property = models.OneToOneField(
        Property,
        on_delete=models.CASCADE,
        related_name="location"
    )

    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100, null=True)
    street = models.CharField(max_length=150, null=True)
    building_number = models.CharField(max_length=20, null=True)

    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True
    )

    metro_station = models.CharField(max_length=100, null=True)
    metro_distance_minutes = models.PositiveSmallIntegerField(null=True)

    def __str__(self):
        return f"{self.city}, {self.street}"


class PropertyPhoto(models.Model):
    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="photos"
    )

    url = models.URLField()
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return self.url

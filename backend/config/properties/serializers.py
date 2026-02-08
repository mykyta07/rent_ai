from rest_framework import serializers
from .models import Property, Location, PropertyPhoto


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            'city', 'district', 'street', 'building_number',
            'latitude', 'longitude', 'metro_station', 'metro_distance_minutes'
        ]


class PropertyPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyPhoto
        fields = ['id', 'url', 'is_main']


class PropertyPhotoCreateSerializer(serializers.ModelSerializer):
    """Серіалізатор для створення фото (без property_id в запиті)"""
    class Meta:
        model = PropertyPhoto
        fields = ['url', 'is_main']


class PropertyListSerializer(serializers.ModelSerializer):
    """Серіалізатор для списку об'єктів (мінімальна інформація)"""
    location = LocationSerializer(read_only=True)
    main_photo = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'price', 'currency',
            'rooms_count', 'total_area', 'realty_type', 'sale_type',
            'location', 'main_photo'
        ]

    def get_main_photo(self, obj):
        main_photo = obj.photos.filter(is_main=True).first()
        if main_photo:
            return main_photo.url
        first_photo = obj.photos.first()
        return first_photo.url if first_photo else None


class PropertyDetailSerializer(serializers.ModelSerializer):
    """Детальний серіалізатор з усією інформацією"""
    location = LocationSerializer(read_only=True)
    photos = PropertyPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = Property
        fields = [
            'id', 'title', 'description',
            'price', 'currency', 'rooms_count', 'total_area',
            'living_area', 'kitchen_area', 'floor', 'floors_count',
            'building_type', 'is_commercial', 'realty_type', 'sale_type',
            'location', 'photos', 'created_at'
        ]


class PropertyCreateSerializer(serializers.ModelSerializer):
    """Серіалізатор для створення нового оголошення"""
    location = LocationSerializer(required=True)
    photos = PropertyPhotoCreateSerializer(many=True, required=False)

    class Meta:
        model = Property
        fields = [
            'title', 'description',
            'price', 'currency', 'rooms_count', 'total_area',
            'living_area', 'kitchen_area', 'floor', 'floors_count',
            'building_type', 'is_commercial', 'realty_type', 'sale_type',
            'location', 'photos'
        ]

    def create(self, validated_data):
        # Витягуємо вкладені дані
        location_data = validated_data.pop('location')
        photos_data = validated_data.pop('photos', [])

        # Створюємо об'єкт нерухомості
        property_obj = Property.objects.create(**validated_data)

        # Створюємо локацію
        Location.objects.create(property=property_obj, **location_data)

        # Створюємо фото
        for photo_data in photos_data:
            PropertyPhoto.objects.create(property=property_obj, **photo_data)

        return property_obj


class PropertyUpdateSerializer(serializers.ModelSerializer):
    """Серіалізатор для оновлення оголошення"""
    location = LocationSerializer(required=False)
    photos = PropertyPhotoCreateSerializer(many=True, required=False)

    class Meta:
        model = Property
        fields = [
            'title', 'description',
            'price', 'currency', 'rooms_count', 'total_area',
            'living_area', 'kitchen_area', 'floor', 'floors_count',
            'building_type', 'is_commercial', 'realty_type', 'sale_type',
            'location', 'photos'
        ]

    def update(self, instance, validated_data):
        # Витягуємо вкладені дані
        location_data = validated_data.pop('location', None)
        photos_data = validated_data.pop('photos', None)

        # Оновлюємо основні поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Оновлюємо локацію
        if location_data:
            Location.objects.update_or_create(
                property=instance,
                defaults=location_data
            )

        # Оновлюємо фото (видаляємо старі і додаємо нові)
        if photos_data is not None:
            instance.photos.all().delete()
            for photo_data in photos_data:
                PropertyPhoto.objects.create(property=instance, **photo_data)

        return instance

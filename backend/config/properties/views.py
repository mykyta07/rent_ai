from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Property, PropertyPhoto, Location
from .serializers import (
    PropertyListSerializer, 
    PropertyDetailSerializer,
    PropertyPhotoSerializer,
    LocationSerializer,
    PropertyCreateSerializer,
    PropertyUpdateSerializer
)


@extend_schema(
    tags=['Properties'],
    summary='Список оголошень',
    description='Отримати список всіх оголошень з фільтрами',
    parameters=[
        OpenApiParameter('rooms', OpenApiTypes.INT, description='Кількість кімнат'),
        OpenApiParameter('district', OpenApiTypes.STR, description='Район міста'),
        OpenApiParameter('min_price', OpenApiTypes.NUMBER, description='Мінімальна ціна'),
        OpenApiParameter('max_price', OpenApiTypes.NUMBER, description='Максимальна ціна'),
        OpenApiParameter('type', OpenApiTypes.STR, description='Тип нерухомості (apartment/house)'),
        OpenApiParameter('sale_type', OpenApiTypes.STR, description='Тип угоди (sale/rent)'),
        OpenApiParameter('min_area', OpenApiTypes.NUMBER, description='Мінімальна площа'),
        OpenApiParameter('max_area', OpenApiTypes.NUMBER, description='Максимальна площа'),
        OpenApiParameter('mine', OpenApiTypes.BOOL, description='Тільки мої оголошення (для авторизованих)'),
    ]
)
class PropertyListView(generics.ListAPIView):
    """
    GET /api/properties/
    GET /api/properties/?rooms=2&district=Голосеевский&max_price=60000
    
    Повертає список об'єктів нерухомості з можливістю фільтрації
    """
    queryset = Property.objects.select_related('location').prefetch_related('photos').all()
    serializer_class = PropertyListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['price', 'created_at', 'total_area']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фільтрація по кімнатах
        rooms = self.request.query_params.get('rooms')
        if rooms:
            queryset = queryset.filter(rooms_count=rooms)
        
        # Фільтрація по району
        district = self.request.query_params.get('district')
        if district:
            queryset = queryset.filter(location__district__icontains=district)
        
        # Фільтрація по ціні (мінімальна)
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        # Фільтрація по ціні (максимальна)
        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Фільтрація по типу нерухомості
        realty_type = self.request.query_params.get('type')
        if realty_type:
            queryset = queryset.filter(realty_type=realty_type)
        
        # Фільтрація по типу угоди (продаж/оренда)
        sale_type = self.request.query_params.get('sale_type')
        if sale_type:
            queryset = queryset.filter(sale_type=sale_type)
        
        # Фільтрація по площі
        min_area = self.request.query_params.get('min_area')
        if min_area:
            queryset = queryset.filter(total_area__gte=min_area)
        
        max_area = self.request.query_params.get('max_area')
        if max_area:
            queryset = queryset.filter(total_area__lte=max_area)
        
        # Фільтрація по станції метро
        metro = self.request.query_params.get('metro')
        if metro:
            queryset = queryset.filter(location__metro_station__icontains=metro)

        # Тільки мої оголошення
        mine = self.request.query_params.get('mine')
        if mine and mine.lower() in ('1', 'true', 'yes'):
            if self.request.user.is_authenticated:
                queryset = queryset.filter(owner=self.request.user)
            else:
                queryset = queryset.none()
        
        return queryset


@extend_schema(
    tags=['Properties'],
    summary='Мої оголошення',
    description='Отримати список оголошень, створених поточним користувачем'
)
class MyPropertyListView(generics.ListAPIView):
    """
    GET /api/properties/my/

    Повертає тільки оголошення поточного користувача
    """
    serializer_class = PropertyListSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['price', 'created_at', 'total_area']
    ordering = ['-created_at']

    def get_queryset(self):
        return Property.objects.select_related('location').prefetch_related('photos').filter(
            owner=self.request.user
        )


@extend_schema(
    tags=['Properties'],
    summary='Деталі оголошення',
    description='Отримати повну інформацію про конкретне оголошення'
)
class PropertyDetailView(generics.RetrieveAPIView):
    """
    GET /api/properties/<int:property_id>/
    
    Повертає детальну інформацію про конкретний об'єкт
    """
    queryset = Property.objects.select_related('location').prefetch_related('photos').all()
    serializer_class = PropertyDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    lookup_url_kwarg = 'property_id'


class PropertyPhotosView(generics.ListAPIView):
    """
    GET /api/properties/<int:property_id>/photos/
    
    Повертає список фото конкретного об'єкта
    """
    serializer_class = PropertyPhotoSerializer
    
    def get_queryset(self):
        property_id = self.kwargs['property_id']
        return PropertyPhoto.objects.filter(property_id=property_id)


@extend_schema(
    tags=['Properties'],
    summary='Створити оголошення',
    description='Додати нове оголошення про нерухомість (потрібна авторизація)',
    request=PropertyCreateSerializer,
    responses={201: PropertyDetailSerializer}
)
class PropertyCreateView(generics.CreateAPIView):
    """
    POST /api/properties/
    
    Створює нове оголошення про нерухомість
    """
    queryset = Property.objects.all()
    serializer_class = PropertyCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Зберігаємо оголошення
        property_obj = serializer.save(owner=self.request.user)
        
        # Автоматично генеруємо embedding для RAG пошуку
        try:
            from ai.gemini_service import GeminiService
            from ai.models import PropertyEmbedding
            
            gemini = GeminiService()
            location = property_obj.location if hasattr(property_obj, 'location') else None
            
            # Формуємо текст для embedding
            text_parts = [
                property_obj.title,
                property_obj.description,
                f"Тип: {property_obj.get_realty_type_display()}",
                f"Угода: {property_obj.get_sale_type_display()}",
                f"Кімнат: {property_obj.rooms_count}",
                f"Площа: {property_obj.total_area} м²",
            ]
            
            if location:
                text_parts.extend([
                    f"Місто: {location.city}",
                    f"Район: {location.district or ''}",
                ])
            
            text = "\n".join(filter(None, text_parts))
            embedding = gemini.generate_embedding(text)
            
            # Зберігаємо embedding
            PropertyEmbedding.objects.update_or_create(
                property=property_obj,
                defaults={
                    'embedding': embedding,
                    'model_name': gemini.embedding_model
                }
            )
        except Exception as e:
            # Не падаємо якщо embedding не вдалося створити
            print(f"Warning: Could not generate embedding for property {property_obj.id}: {e}")


@extend_schema(
    tags=['Properties'],
    summary='Оновити оголошення',
    description='Повністю оновити оголошення (PUT) або частково (PATCH)',
    request=PropertyUpdateSerializer,
    responses={200: PropertyDetailSerializer}
)
class PropertyUpdateView(generics.UpdateAPIView):
    """
    PUT /api/properties/<int:property_id>/
    PATCH /api/properties/<int:property_id>/
    
    Оновлює існуюче оголошення
    """
    queryset = Property.objects.all()
    serializer_class = PropertyUpdateSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'property_id'

    def get_queryset(self):
        queryset = Property.objects.all()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(owner=self.request.user)
    
    def perform_update(self, serializer):
        # Оновлюємо оголошення
        property_obj = serializer.save()
        
        # Регенеруємо embedding (бо дані змінились)
        try:
            from ai.gemini_service import GeminiService
            from ai.models import PropertyEmbedding
            
            gemini = GeminiService()
            location = property_obj.location if hasattr(property_obj, 'location') else None
            
            # Формуємо текст для embedding
            text_parts = [
                property_obj.title,
                property_obj.description,
                f"Тип: {property_obj.get_realty_type_display()}",
                f"Угода: {property_obj.get_sale_type_display()}",
                f"Кімнат: {property_obj.rooms_count}",
                f"Площа: {property_obj.total_area} м²",
            ]
            
            if location:
                text_parts.extend([
                    f"Місто: {location.city}",
                    f"Район: {location.district or ''}",
                ])
            
            text = "\n".join(filter(None, text_parts))
            embedding = gemini.generate_embedding(text)
            
            # Оновлюємо embedding
            PropertyEmbedding.objects.update_or_create(
                property=property_obj,
                defaults={
                    'embedding': embedding,
                    'model_name': gemini.embedding_model
                }
            )
        except Exception as e:
            # Не падаємо якщо embedding не вдалося оновити
            print(f"Warning: Could not update embedding for property {property_obj.id}: {e}")


@extend_schema(
    tags=['Properties'],
    summary='Видалити оголошення',
    description='Видалити оголошення назавжди (потрібна авторизація)',
    responses={204: None}
)
class PropertyDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/properties/<int:property_id>/
    
    Видаляє оголошення
    """
    queryset = Property.objects.all()
    serializer_class = PropertyDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'property_id'

    def get_queryset(self):
        queryset = Property.objects.all()
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(owner=self.request.user)


class PropertyLocationView(APIView):
    """
    GET /api/properties/<int:property_id>/location/
    
    Повертає інформацію про локацію об'єкта
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @extend_schema(
        tags=['Properties'],
        summary='Локація оголошення',
        description='Отримати детальну інформацію про місцезнаходження'
    )
    def get(self, request, property_id):
        try:
            location = Location.objects.get(property_id=property_id)
            serializer = LocationSerializer(location)
            return Response(serializer.data)
        except Location.DoesNotExist:
            return Response(
                {'error': 'Локація не знайдена'},
                status=status.HTTP_404_NOT_FOUND
            )

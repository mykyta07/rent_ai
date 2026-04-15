from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .serializers import (
    ChatRequestSerializer,
    ChatResponseSerializer,
    ChatHistoryMessageSerializer,
    SemanticSearchRequestSerializer,
    SemanticSearchResponseSerializer,
    ExplainRequestSerializer,
    ExplainBriefRequestSerializer,
    CompareRequestSerializer,
    ListingDescriptionGenerateSerializer,
)
from .models import ChatMessage
from .gemini_service import GeminiService
from properties.models import Property


class ChatAssistantView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChatRequestSerializer
    
    """
    POST /api/ai/chat/
    
    Чат-асистент на базі Gemini, який має доступ до бази даних нерухомості.
    Користувач визначається автоматично з JWT токену.
    
    Тіло запиту:
    {
        "message": "Хочу квартиру на 2 кімнати до 60 000$ у Голосеєвському районі"
    }
    
    Відповідь:
    {
        "assistant_message": "Я знайшов 3 варіанти...",
        "properties": [1, 5, 12]
    }
    """
    
    def post(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Отримуємо користувача з JWT токену
        user = request.user
        message = serializer.validated_data['message']
        
        # Отримуємо останні 10 повідомлень для контексту
        conversation_history = ChatMessage.objects.filter(
            user=user
        ).order_by('-created_at')[:10][::-1]
        
        # Викликаємо Gemini сервіс
        gemini_service = GeminiService()
        try:
            result = gemini_service.generate_chat_response(
                user_message=message,
                user_id=user.id,
                conversation_history=conversation_history
            )
            
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Помилка при обробці запиту: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    """
    GET /api/ai/chat/history/?limit=50

    Повертає останні повідомлення поточного користувача.
    За замовчуванням повертає 50, максимум 200.
    """

    def get(self, request):
        raw_limit = request.query_params.get('limit', 50)
        try:
            limit = max(1, min(int(raw_limit), 200))
        except (TypeError, ValueError):
            return Response(
                {'error': 'Параметр limit має бути числом від 1 до 200'},
                status=status.HTTP_400_BAD_REQUEST
            )

        messages = ChatMessage.objects.filter(
            user=request.user
        ).order_by('-created_at')[:limit]

        # Повертаємо від старих до нових для зручного рендеру в UI
        serializer = ChatHistoryMessageSerializer(messages[::-1], many=True)
        return Response(
            {
                'count': len(serializer.data),
                'limit': limit,
                'results': serializer.data
            },
            status=status.HTTP_200_OK
        )


class SemanticSearchView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = SemanticSearchRequestSerializer
    
    """
    POST /api/ai/search/
    
    Семантичний пошук об'єктів нерухомості за описом через embeddings
    
    Тіло запиту:
    {
        "query": "Світла квартира з панорамними вікнами і видом на парк"
    }
    
    Відповідь: список об'єктів з оцінкою релевантності
    """
    
    def post(self, request):
        serializer = SemanticSearchRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['query']
        
        gemini_service = GeminiService()
        try:
            results = gemini_service.semantic_search(query, top_k=10)
            
            response_data = [
                {
                    'property_id': item['property'].id,
                    'title': item['property'].title,
                    'description': item['property'].description[:200] + '...',
                    'similarity_score': float(item['similarity_score'])
                }
                for item in results
            ]
            
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Помилка при пошуку: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExplainPropertyView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExplainRequestSerializer
    
    """
    POST /api/ai/explain/
    
    Пояснює, чому обрано конкретний об'єкт
    
    Тіло запиту:
    {
        "property_id": 5,
        "user_preferences": "Шукаю квартиру для сім'ї з дитиною"
    }
    """
    
    def post(self, request):
        serializer = ExplainRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        property_id = serializer.validated_data['property_id']
        user_preferences = serializer.validated_data.get('user_preferences', '')
        
        # Перевіряємо, чи існує об'єкт
        if not Property.objects.filter(id=property_id).exists():
            return Response(
                {'error': 'Об\'єкт не знайдено'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        gemini_service = GeminiService()
        try:
            explanation = gemini_service.explain_property(
                property_id=property_id,
                user_preferences=user_preferences
            )
            
            return Response(
                {'explanation': explanation},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': f'Помилка при поясненні: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExplainPropertyBriefView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExplainBriefRequestSerializer

    """
    POST /api/ai/explain/brief/

    Повертає короткий аналіз об'єкта (2-3 речення) для картки на сторінці оголошення.
    """

    def post(self, request):
        serializer = ExplainBriefRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        property_id = serializer.validated_data['property_id']
        if not Property.objects.filter(id=property_id).exists():
            return Response(
                {'error': 'Об\'єкт не знайдено'},
                status=status.HTTP_404_NOT_FOUND
            )

        gemini_service = GeminiService()
        try:
            explanation = gemini_service.explain_property_brief(property_id=property_id)
            return Response({'explanation': explanation}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Помилка при короткому аналізі: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GenerateListingDescriptionView(APIView):
    """
    POST /api/ai/generate-listing-description/

    Тіло: поля з форми оголошення (title, city, price, realty_type, …).
    Відповідь: { "description": "..." }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ListingDescriptionGenerateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        title = (data.get("title") or "").strip()
        city = (data.get("city") or "").strip()
        hints = (data.get("hints") or "").strip()
        if not title and not city and not hints:
            return Response(
                {
                    "error": "Вкажіть хоча б місто, заголовок або поле «підказка», щоб згенерувати опис.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        gemini_service = GeminiService()
        try:
            description = gemini_service.generate_listing_description(data)
            return Response({"description": description}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ComparePropertiesView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CompareRequestSerializer
    
    """
    POST /api/ai/compare/
    
    Порівнює 2-3 об'єкти і повертає текстове резюме
    
    Тіло запиту:
    {
        "property_ids": [1, 5, 12]
    }
    """
    
    def post(self, request):
        serializer = CompareRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        property_ids = serializer.validated_data['property_ids']
        
        # Перевіряємо, чи всі об'єкти існують
        existing_count = Property.objects.filter(id__in=property_ids).count()
        if existing_count != len(property_ids):
            return Response(
                {'error': 'Деякі об\'єкти не знайдено'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        gemini_service = GeminiService()
        try:
            comparison = gemini_service.compare_properties(property_ids)
            
            return Response(
                {'comparison': comparison},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': f'Помилка при порівнянні: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

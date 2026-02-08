from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .serializers import (
    ChatRequestSerializer,
    ChatResponseSerializer,
    SemanticSearchRequestSerializer,
    SemanticSearchResponseSerializer,
    ExplainRequestSerializer,
    CompareRequestSerializer
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

import google.generativeai as genai
from django.conf import settings
from properties.models import Property
from ai.models import PropertyEmbedding, ChatMessage
import numpy as np
import json


class GeminiService:
    """Сервіс для роботи з Gemini API"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Gemini Flash Latest - найновіша стабільна версія
        self.model = genai.GenerativeModel('models/gemini-flash-latest')
        self.embedding_model = 'models/text-embedding-004'
    
    def generate_chat_response(self, user_message, user_id, conversation_history=None):
        """
        Генерує відповідь чат-асистента з RAG (Retrieval Augmented Generation)
        Спочатку знаходить релевантні об'єкти через embeddings, потім аналізує їх
        """
        # КРОК 1: RETRIEVAL - Семантичний пошук найрелевантніших об'єктів
        # =================================================================
        relevant_results = self.semantic_search(query=user_message, top_k=10)
        
        # Якщо не знайдено релевантних - використовуємо фільтри
        if not relevant_results:
            properties = Property.objects.select_related('location').all()[:10]
            relevant_results = [
                {'property': prop, 'similarity_score': 0.0} 
                for prop in properties
            ]
        
        # КРОК 2: AUGMENTED - Форматуємо контекст з найрелевантнішими об'єктами
        # =======================================================================
        properties_context = self._format_rag_context(relevant_results)
        
        # Історія розмови (останні 5 повідомлень)
        history_text = ""
        if conversation_history:
            history_text = "\n".join([
                f"{msg.role}: {msg.content}" 
                for msg in conversation_history[-5:]  # Тільки останні 5
            ])
        
        # Загальна статистика БД
        total_properties = Property.objects.count()
        
        # КРОК 3: GENERATION - Gemini генерує відповідь з контекстом
        # ===========================================================
        prompt = f"""
Ти - AI асистент з нерухомості. Твоя задача - допомагати користувачам знаходити підходящу нерухомість.

ІСТОРІЯ РОЗМОВИ:
{history_text}

ПОВІДОМЛЕННЯ КОРИСТУВАЧА:
{user_message}

НАЙБІЛЬШ РЕЛЕВАНТНІ ОБ'ЄКТИ (топ-10 з {total_properties} в базі):
{properties_context}

ІНСТРУКЦІЇ:
1. Проаналізуй запит користувача
2. Визнач чи користувач шукає ОРЕНДУ чи ПРОДАЖ (ключові слова: орендувати, знімати, здати, rent - це оренда; купити, придбати, продаж, buy - це продаж)
3. З наданого списку об'єктів обери найкращі 3-5 варіантів за критеріями:
   - Тип угоди (Оренда/Продаж)
   - Кількість кімнат
   - Локація (місто, район)
   - Ціна (УВАГА: ціни в грн або $ - не плутай!)
   - Релевантність запиту (скор подібності)
4. Надай конкретні рекомендації з ID об'єктів у форматі "ID: X"
5. Поясни чому саме ці об'єкти підходять
6. Будь дружнім та професійним
7. Відповідай українською мовою

ВАЖЛИВО: 
- У тебе є доступ ТІЛЬКИ до цих 10 об'єктів (вони найрелевантніші з усієї бази)
- Якщо користувач шукає оренду - показуй ТІЛЬКИ об'єкти з типом "Оренда"
- Якщо користувач шукає купівлю - показуй ТІЛЬКИ об'єкти з типом "Продаж"
- Завжди вказуй ID об'єктів у форматі "ID: X"
- Ціни можуть бути в $ (доларах) або грн (гривнях) - вказуй валюту!
- Оренда зазвичай в гривнях (грн), продаж - в доларах ($)
- Скор релевантності показує наскільки об'єкт відповідає запиту (0-100%)
"""
        
        response = self.model.generate_content(prompt)
        
        # Зберігаємо повідомлення в БД
        ChatMessage.objects.create(
            user_id=user_id,
            role='user',
            content=user_message
        )
        ChatMessage.objects.create(
            user_id=user_id,
            role='assistant',
            content=response.text
        )
        
        # Аналізуємо відповідь для виявлення згаданих ID
        properties_list = [r['property'] for r in relevant_results]
        mentioned_property_ids = self._extract_property_ids(response.text, properties_list)
        
        return {
            'assistant_message': response.text,
            'properties': mentioned_property_ids,
            'total_in_db': total_properties,
            'searched_count': len(relevant_results),
            'relevance_scores': [r['similarity_score'] for r in relevant_results[:5]]
        }
    
    def generate_embedding(self, text):
        """
        Генерує embedding для тексту через Gemini
        """
        result = genai.embed_content(
            model=self.embedding_model,
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    
    def semantic_search(self, query, top_k=5):
        """
        Семантичний пошук об'єктів за описом
        """
        # Генеруємо embedding для запиту
        query_embedding = genai.embed_content(
            model=self.embedding_model,
            content=query,
            task_type="retrieval_query"
        )['embedding']
        
        # Отримуємо всі embedding з БД
        property_embeddings = PropertyEmbedding.objects.select_related(
            'property', 'property__location'
        ).all()
        
        if not property_embeddings:
            # Якщо embeddings не створені, створюємо їх
            self._create_embeddings_for_all_properties()
            property_embeddings = PropertyEmbedding.objects.select_related(
                'property', 'property__location'
            ).all()
        
        # Обчислюємо косинусну схожість
        results = []
        for prop_emb in property_embeddings:
            doc_embedding = prop_emb.embedding
            similarity = self._cosine_similarity(query_embedding, doc_embedding)
            results.append({
                'property': prop_emb.property,
                'similarity_score': similarity
            })
        
        # Сортуємо за схожістю
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return results[:top_k]
    
    def explain_property(self, property_id, user_preferences=""):
        """
        Пояснює, чому обрано конкретний об'єкт
        """
        try:
            property_obj = Property.objects.select_related('location').get(id=property_id)
        except Property.DoesNotExist:
            return "Об'єкт не знайдено"
        
        property_info = self._format_single_property(property_obj)
        
        prompt = f"""
Ти - експерт з нерухомості. Поясни, чому цей об'єкт може бути хорошим вибором.

ІНФОРМАЦІЯ ПРО ОБ'ЄКТ:
{property_info}

ПЕРЕВАГИ КОРИСТУВАЧА:
{user_preferences if user_preferences else "Не вказано"}

Надай детальне пояснення переваг та недоліків об'єкта. Відповідай українською мовою.
"""
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def compare_properties(self, property_ids):
        """
        Порівнює 2-3 об'єкти і повертає текстове резюме
        """
        properties = Property.objects.select_related('location').filter(
            id__in=property_ids
        )
        
        if properties.count() < 2:
            return "Недостатньо об'єктів для порівняння"
        
        comparison_data = "\n\n".join([
            f"ОБ'ЄКТ {i+1} (ID: {prop.id}):\n{self._format_single_property(prop)}"
            for i, prop in enumerate(properties)
        ])
        
        prompt = f"""
Ти - експерт з нерухомості. Порівняй наступні об'єкти:

{comparison_data}

Надай детальне порівняння за критеріями:
- Ціна та співвідношення ціна/якість
- Локація та інфраструктура
- Площа та планування
- Стан та характеристики будинку
- Загальна рекомендація

Відповідай українською мовою.
"""
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def _format_properties_context(self, properties, limit=50):
        """Форматує список об'єктів для контексту (старий метод для сумісності)"""
        context_parts = []
        for prop in properties[:limit]:
            location = prop.location if hasattr(prop, 'location') else None
            district = location.district if location else "Не вказано"
            
            # Визначаємо тип угоди
            sale_type_display = "Продаж" if prop.sale_type == "sale" else "Оренда"
            
            context_parts.append(
                f"ID: {prop.id} | {sale_type_display} | {prop.title} | "
                f"{prop.rooms_count} кімн. | {prop.total_area} м² | "
                f"{prop.price} {prop.currency} | Район: {district}"
            )
        
        return "\n".join(context_parts)
    
    def _format_rag_context(self, relevant_results):
        """
        Форматує результати RAG пошуку для промпту Gemini
        Включає скор релевантності та детальну інформацію
        """
        context_parts = []
        
        for i, result in enumerate(relevant_results, 1):
            prop = result['property']
            score = result['similarity_score']
            location = prop.location if hasattr(prop, 'location') else None
            
            # Визначаємо тип угоди
            sale_type_display = "Оренда" if prop.sale_type == "rent" else "Продаж"
            
            # Форматуємо опис (обрізаємо якщо занадто довгий)
            description = prop.description[:150] + "..." if len(prop.description) > 150 else prop.description
            
            context_parts.append(f"""
[Об'єкт #{i}] ID: {prop.id} | Релевантність: {score:.1%}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Тип угоди: {sale_type_display}
Назва: {prop.title}
Опис: {description}
Ціна: {prop.price:,.0f} {prop.currency}
Характеристики: {prop.rooms_count} кімн. | {prop.total_area}м² | {prop.floor}/{prop.floors_count} поверх
Локація: {location.city if location else '?'}, {location.district if location else '?'}, {location.street if location else '?'}
""")
        
        return "\n".join(context_parts)
    
    def _format_single_property(self, prop):
        """Форматує один об'єкт для детального аналізу"""
        location = prop.location if hasattr(prop, 'location') else None
        
        return f"""
Назва: {prop.title}
Опис: {prop.description}
Ціна: {prop.price} {prop.currency}
Тип: {prop.get_realty_type_display()}
Тип угоди: {prop.get_sale_type_display()}
Кімнат: {prop.rooms_count}
Загальна площа: {prop.total_area} м²
Житлова площа: {prop.living_area} м²
Площа кухні: {prop.kitchen_area} м²
Поверх: {prop.floor} з {prop.floors_count}
Тип будинку: {prop.building_type}
Локація: {location.district if location else 'Не вказано'}, {location.street if location else ''}
Метро: {location.metro_station if location and location.metro_station else 'Не вказано'} ({location.metro_distance_minutes if location and location.metro_distance_minutes else '?'} хв)
"""
    
    def _extract_property_ids(self, text, properties):
        """Витягує ID об'єктів, згаданих у відповіді"""
        mentioned_ids = []
        for prop in properties:
            if f"ID: {prop.id}" in text or f"#{prop.id}" in text:
                mentioned_ids.append(prop.id)
        return mentioned_ids
    
    def _cosine_similarity(self, vec1, vec2):
        """Обчислює косинусну схожість між двома векторами"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    def _create_embeddings_for_all_properties(self):
        """Створює embeddings для всіх об'єктів без них"""
        from django.db.models import Q
        
        # Знаходимо об'єкти без embeddings
        properties_without_embeddings = Property.objects.filter(
            Q(embedding__isnull=True) | ~Q(id__in=PropertyEmbedding.objects.values_list('property_id', flat=True))
        )
        
        print(f"Створюю embeddings для {properties_without_embeddings.count()} об'єктів...")
        
        for i, prop in enumerate(properties_without_embeddings, 1):
            try:
                # Формуємо текст для embedding (включаємо всю важливу інформацію)
                location = prop.location if hasattr(prop, 'location') else None
                text = f"""
{prop.title}
{prop.description}
Тип: {prop.get_realty_type_display()}
Тип угоди: {prop.get_sale_type_display()}
Кімнат: {prop.rooms_count}
Площа: {prop.total_area} м²
Локація: {location.city if location else ''} {location.district if location else ''} {location.street if location else ''}
                """.strip()
                
                embedding = self.generate_embedding(text)
                
                # Видаляємо старий embedding якщо є (на випадок дублікатів)
                PropertyEmbedding.objects.filter(property=prop).delete()
                
                # Створюємо новий
                PropertyEmbedding.objects.create(
                    property=prop,
                    embedding=embedding,
                    model_name=self.embedding_model
                )
                
                print(f"✓ {i}/{properties_without_embeddings.count()} - ID:{prop.id} - {prop.title[:50]}")
                
            except Exception as e:
                print(f"✗ Помилка для ID:{prop.id} - {str(e)}")
                continue
        
        print(f"✅ Створено embeddings для {properties_without_embeddings.count()} об'єктів!")

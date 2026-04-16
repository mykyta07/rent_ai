import google.generativeai as genai
from django.conf import settings
from properties.models import Property
from ai.models import PropertyEmbedding, ChatMessage
import numpy as np
import json
import re
from ai.models import PropertyExplainChatMessage


class GeminiService:
    """Сервіс для роботи з Gemini API"""
    
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        # Gemini Flash Latest - найновіша стабільна версія
        self.model = genai.GenerativeModel('models/gemini-flash-latest')
        self.embedding_model = 'models/gemini-embedding-001'
    
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
        
        # Історія розмови (останні 5 повідомлень)
        history_text = ""
        if conversation_history:
            history_text = "\n".join([
                f"{msg.role}: {msg.content}" 
                for msg in conversation_history[-5:]  # Тільки останні 5
            ])
        
        # Загальна статистика БД
        total_properties = Property.objects.count()
        
        specific_question = self._is_specific_property_question(user_message)
        focus_entries = (
            self._build_focus_entries(user_message, relevant_results)
            if specific_question
            else None
        )
        chat_mode = "focus" if (specific_question and focus_entries) else "search"

        # КРОК 2: AUGMENTED — контекст: один об'єкт (повні дані) або топ-10 RAG
        if chat_mode == "focus":
            properties_context = self._format_focus_property_context(focus_entries)
            recommendation_policy = (
                "РЕЖИМ ОДНОГО ОБ'ЄКТА (або явно названих у блоці контексту). "
                "Відповідай лише про ці оголошення. Не згадуй інші ID, не пропонуй альтернативи й "
                "не закінчуй фразами на кшталт «ось ще варіанти». Якщо чогось немає в даних — скажи, що в базі цього немає."
            )
            instructions_block = """
ІНСТРУКЦІЇ:
1. Відповідай українською, по суті запиту користувача.
2. Спирайся лише на факти з блоку контексту вище; не вигадуй нові об'єкти, ціни чи адреси.
3. Якщо в запиті фігурує оренда чи продаж — коротко узгодь формулювання з полем «Тип угоди» в даних.
4. Можна один раз зазначити ID у форматі «ID: X», якщо це допомагає користувачу.
5. Формат відповіді: простий текст без Markdown (#, **, *, ```), без зайвих службових символів.
"""
            context_header = (
                f"ДАНІ ПРО ОБ'ЄКТ(И) ДЛЯ ВІДПОВІДІ (повний опис з бази; не показуй користувачу службові пояснення, лише зміст):"
            )
        else:
            properties_context = self._format_rag_context(relevant_results)
            recommendation_policy = (
                "Користувач у режимі пошуку варіантів. "
                "Доречно запропонувати 2-5 релевантних об'єктів і запросити уточнення критеріїв."
            )
            instructions_block = f"""
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
8. Формат відповіді: простий текст без Markdown (#, **, *, ```), без зайвих службових символів

ВАЖЛИВО: 
- У тебе є доступ ТІЛЬКИ до цих 10 об'єктів (вони найрелевантніші з усієї бази)
- Якщо користувач шукає оренду - показуй ТІЛЬКИ об'єкти з типом "Оренда"
- Якщо користувач шукає купівлю - показуй ТІЛЬКИ об'єкти з типом "Продаж"
- Завжди вказуй ID об'єктів у форматі "ID: X"
- Ціни можуть бути в $ (доларах) або грн (гривнях) - вказуй валюту!
- Оренда зазвичай в гривнях (грн), продаж - в доларах ($)
- Скор релевантності показує наскільки об'єкт відповідає запиту (0-100%)
"""
            context_header = (
                f"НАЙБІЛЬШ РЕЛЕВАНТНІ ОБ'ЄКТИ (топ-10 з {total_properties} в базі):"
            )

        # КРОК 3: GENERATION - Gemini генерує відповідь з контекстом
        # ===========================================================
        prompt = f"""
Ти - AI асистент з нерухомості. Твоя задача - допомагати користувачам знаходити підходящу нерухомість.

ІСТОРІЯ РОЗМОВИ:
{history_text}

ПОВІДОМЛЕННЯ КОРИСТУВАЧА:
{user_message}

{context_header}
{properties_context}
{instructions_block}

ПОЛІТИКА ВІДПОВІДІ ДЛЯ ЦЬОГО ЗАПИТУ:
{recommendation_policy}
"""
        
        response = self.model.generate_content(prompt)
        assistant_text = self._clean_llm_text(response.text)
        
        # Аналізуємо відповідь для виявлення згаданих ID (у фокус-режимі — лише дозволені)
        effective = focus_entries if chat_mode == "focus" else relevant_results
        properties_list = [r['property'] for r in effective]
        allowed_ids = {p.id for p in properties_list}
        mentioned_property_ids = [
            i for i in self._extract_property_ids(assistant_text, properties_list)
            if i in allowed_ids
        ]

        # Зберігаємо повідомлення в БД (разом з рекомендованими ID для історії)
        ChatMessage.objects.create(
            user_id=user_id,
            role='user',
            content=user_message,
            properties=[],
        )
        ChatMessage.objects.create(
            user_id=user_id,
            role='assistant',
            content=assistant_text,
            properties=mentioned_property_ids,
        )
        
        return {
            'assistant_message': assistant_text,
            'properties': mentioned_property_ids,
            'total_in_db': total_properties,
            'searched_count': len(relevant_results),
            'relevance_scores': [r['similarity_score'] for r in relevant_results[:5]]
        }

    def generate_property_explain_chat_response(
        self, user_message, user_id, property_id, conversation_history=None
    ):
        """
        Чат-пояснення для конкретного об'єкта.
        Історія: PropertyExplainChatMessage (user + property).
        """
        if conversation_history is None:
            conversation_history = []

        prop = Property.objects.select_related("location").get(pk=property_id)

        history_text = ""
        if conversation_history:
            history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in conversation_history[-12:]])

        property_context = self._format_single_property(prop)

        prompt = f"""
Ти - AI асистент з нерухомості. Користувач спілкується про ОДИН конкретний об'єкт.

ОБ'ЄКТ (дані з бази):
{property_context}

ІСТОРІЯ ДІАЛОГУ:
{history_text if history_text else "Немає попередньої історії"}

ПОВІДОМЛЕННЯ КОРИСТУВАЧА:
{user_message}

ПРАВИЛА:
- Відповідай лише про цей об'єкт (ID: {property_id}). НЕ пропонуй альтернативи і не згадуй інші ID.
- Не вигадуй дані, яких немає в описі/полях об'єкта.
- Якщо бракує даних для точної відповіді — скажи, що в базі цього немає, і уточни, що саме користувач хоче дізнатись (стан меблів, комунальні, тварини, застава тощо).
- Формат: простий текст українською без Markdown (#, **, *, ```), без емодзі.
"""

        response = self.model.generate_content(prompt)
        assistant_text = self._clean_llm_text(response.text)

        PropertyExplainChatMessage.objects.create(
            user_id=user_id,
            property_id=property_id,
            role="user",
            content=user_message,
        )
        PropertyExplainChatMessage.objects.create(
            user_id=user_id,
            property_id=property_id,
            role="assistant",
            content=assistant_text,
        )

        return {"assistant_message": assistant_text}

    def _is_specific_property_question(self, user_message):
        """
        Евристика: відрізняє конкретне питання від запиту «підбери варіанти».
        True -> не нав'язуємо додаткові пропозиції.
        """
        text = (user_message or "").strip().lower()
        if not text:
            return False

        if self._extract_explicit_property_ids_from_user(user_message):
            return True

        # Явний пошуковий намір
        discovery_markers = [
            "підбери",
            "підберіть",
            "знайди",
            "знайдіть",
            "покажи варіанти",
            "які є варіанти",
            "що є",
            "порадь",
            "recommend",
            "show me",
            "find me",
            "схожі",
            "альтернатив",
            "інші варіанти",
            "ще якісь",
            "підбір",
        ]
        if any(m in text for m in discovery_markers):
            return False

        # Точкове питання / деталі про обране оголошення
        tangible = [
            "цей об",
            "ця квартира",
            "цю квартиру",
            "цей будинок",
            "цей варіант",
            "цього варіанту",
            "про цей",
            "про цю",
            "це оголошення",
            "детальніше",
            "детальніш",
            "розкажи",
            "розпові",
            "більше про",
            "ще про",
        ]
        if any(m in text for m in tangible):
            return True

        # Точкове питання/аналіз
        specific_markers = [
            "конкретно",
            "чи варто",
            "поясни",
            "пояснення",
            "які мінуси",
            "які ризики",
            "оцін",
            "порівняй",
            "чому",
            "наскільки",
            "what about",
        ]
        if any(m in text for m in specific_markers):
            return True

        return False

    def _extract_explicit_property_ids_from_user(self, user_message):
        """ID з тексту користувача: «ID: 178», «ід 178», «#178», «№ 178»."""
        text = user_message or ""
        ids = set()
        for m in re.finditer(r"(?i)(?:\bID\b|\bід\b)\s*[:#]?\s*(\d+)", text):
            ids.add(int(m.group(1)))
        for m in re.finditer(r"(?:^|[\s,;])(?:#|№)\s*(\d+)(?=[\s,;.]|$)", text):
            ids.add(int(m.group(1)))
        return sorted(ids)

    def _normalize_addr_tokens(self, s):
        s = (s or "").lower()
        s = re.sub(r"[^\w\u0400-\u04FF]+", " ", s)
        return [t for t in s.split() if len(t) > 2]

    def _match_focus_from_user_paste(self, user_message, relevant_results):
        """Зіставити вулицю / демонстратив «цей варіант» з топом RAG."""
        if not user_message or not relevant_results:
            return None
        text_lower = user_message.lower()
        demonstrative = (
            "цей варіант", "цього варіанту", "цю квартиру", "цю нерухомість",
            "цей об'єкт", "цього об'єкта", "про цей", "про цю", "це оголошення",
        )
        street_m = re.search(
            r"(?i)(вул\.?\s*[^,\n]+|вулиця\s+[^,\n]+|просп\.?\s*[^,\n]+|проспект\s+[^,\n]+)",
            user_message,
        )
        user_tokens = self._normalize_addr_tokens(user_message)
        best = None
        best_score = 0
        for r in relevant_results:
            p = r["property"]
            loc = p.location if hasattr(p, "location") else None
            hay_list = self._normalize_addr_tokens(
                f"{p.title} {getattr(loc, 'street', '') or ''} {getattr(loc, 'city', '') or ''}"
            )
            hay_set = set(hay_list)
            score = 0
            if street_m:
                frag_tokens = self._normalize_addr_tokens(street_m.group(0))
                score += sum(2 for t in frag_tokens if t in hay_set)
            if any(d in text_lower for d in demonstrative):
                score += sum(1 for t in user_tokens if t in hay_set)
            if score > best_score:
                best_score = score
                best = r
        if best and best_score >= 2:
            return best
        return None

    def _build_focus_entries(self, user_message, relevant_results):
        """
        Список записів як у semantic_search для режиму «один об'єкт».
        """
        explicit_ids = self._extract_explicit_property_ids_from_user(user_message)
        if explicit_ids:
            out = []
            by_id = {r["property"].id: r for r in relevant_results}
            for pid in explicit_ids:
                if pid in by_id:
                    out.append(by_id[pid])
                else:
                    try:
                        p = Property.objects.select_related("location").get(pk=pid)
                        out.append({"property": p, "similarity_score": 0.0})
                    except Property.DoesNotExist:
                        pass
            return out or None

        match = self._match_focus_from_user_paste(user_message, relevant_results)
        if match:
            return [match]
        if relevant_results:
            return [relevant_results[0]]
        return None

    def _format_focus_property_context(self, focus_entries):
        """Повний опис обраних об'єктів (без обрізання description)."""
        if len(focus_entries) == 1:
            p = focus_entries[0]["property"]
            return (
                f"ОБ'ЄКТ ID {p.id}. Використовуй лише ці дані:\n"
                + self._format_single_property(p)
            )
        blocks = []
        for e in focus_entries:
            p = e["property"]
            blocks.append(f"--- ID: {p.id} ---\n" + self._format_single_property(p))
        return "ОБ'ЄКТИ (лише вони):\n\n" + "\n\n".join(blocks)

    def _clean_llm_text(self, text):
        """
        Нормалізує текст відповіді моделі для UI чату:
        - прибирає markdown-обгортки і зайві символи;
        - уніфікує списки;
        - чистить надлишкові порожні рядки.
        """
        if not text:
            return ""
        cleaned = str(text).replace("\r\n", "\n").replace("\r", "\n")
        cleaned = cleaned.replace("```", "")
        cleaned = cleaned.replace("**", "").replace("__", "").replace("`", "")
        lines = []
        for raw in cleaned.split("\n"):
            line = raw.strip()
            if not line:
                lines.append("")
                continue
            # Забираємо markdown-заголовки
            while line.startswith("#"):
                line = line[1:].lstrip()
            # Уніфікуємо маркери списку
            if line.startswith("- ") or line.startswith("* "):
                line = f"• {line[2:].strip()}"
            lines.append(line)
        # Прибираємо надлишок порожніх рядків
        out = []
        empty_streak = 0
        for line in lines:
            if line == "":
                empty_streak += 1
                if empty_streak <= 1:
                    out.append(line)
            else:
                empty_streak = 0
                out.append(line)
        return "\n".join(out).strip()
    
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
        query_embedding_len = len(query_embedding)
        
        for prop_emb in property_embeddings:
            doc_embedding = prop_emb.embedding
            
            # Перевіряємо сумісність розмірів embeddings
            if len(doc_embedding) != query_embedding_len:
                # Пропускаємо embeddings з несумісними розмірами
                # (це може трапитися при переходу на новий embedding model)
                print(f"⚠️  Пропуск ID:{prop_emb.property.id} - "
                      f"несумісний розмір embedding ({len(doc_embedding)} vs {query_embedding_len})")
                continue
            
            try:
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                results.append({
                    'property': prop_emb.property,
                    'similarity_score': similarity
                })
            except Exception as e:
                print(f"⚠️  Помилка при обчисленні подібності для ID:{prop_emb.property.id}: {e}")
                continue
        
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

    def explain_property_brief(self, property_id):
        """
        Короткий аналіз об'єкта (2-3 речення) для відображення в сайдбарі сторінки.
        """
        try:
            property_obj = Property.objects.select_related('location').get(id=property_id)
        except Property.DoesNotExist:
            return "Об'єкт не знайдено"

        property_info = self._format_single_property(property_obj)
        prompt = f"""
Ти - експерт з нерухомості. Зроби дуже короткий аналіз оголошення на 2-3 речення українською.

ІНФОРМАЦІЯ ПРО ОБ'ЄКТ:
{property_info}

ВИМОГИ:
- Пиши коротко та практично, без загальних фраз.
- Обов'язково вкажи 1-2 ключові переваги.
- Обов'язково вкажи 1 можливий нюанс/ризик.
- Не використовуй марковані списки, тільки суцільний текст.
- Максимум 420 символів.
"""
        response = self.model.generate_content(prompt)
        return response.text

    def generate_listing_description(self, context: dict) -> str:
        """
        Генерує текст оголошення українською за заповненими полями форми (без звернення до БД).
        """
        rt = context.get("realty_type") or "apartment"
        type_ua = {"apartment": "квартира", "house": "будинок", "commercial": "комерційна нерухомість"}.get(
            rt, "квартира"
        )
        deal = "оренда" if context.get("sale_type") == "rent" else "продаж"
        parts = [
            f"Тип об'єкта: {type_ua}",
            f"Тип угоди: {deal}",
        ]
        if (context.get("title") or "").strip():
            parts.append(f"Заголовок (орієнтир): {context['title'].strip()}")
        loc_bits = []
        for key, label in (
            ("city", "Місто"),
            ("district", "Район"),
            ("street", "Вулиця"),
            ("building_number", "Номер будинку"),
            ("metro_station", "Метро"),
        ):
            v = context.get(key)
            if v is not None and str(v).strip():
                loc_bits.append(f"{label}: {str(v).strip()}")
        if context.get("metro_distance_minutes") is not None:
            loc_bits.append(f"До метро: {context['metro_distance_minutes']} хв.")
        if loc_bits:
            parts.append("Локація: " + "; ".join(loc_bits))

        price = context.get("price")
        cur = (context.get("currency") or "$").strip() or "$"
        if price is not None and price > 0:
            parts.append(f"Ціна: {price} {cur}")
        else:
            parts.append("Ціна: не вказана або договірна")

        for key, label in (
            ("rooms_count", "Кімнат"),
            ("total_area", "Загальна площа, м²"),
            ("living_area", "Житлова площа, м²"),
            ("kitchen_area", "Кухня, м²"),
            ("floor", "Поверх"),
            ("floors_count", "Поверховість будинку"),
        ):
            v = context.get(key)
            if v is not None:
                parts.append(f"{label}: {v}")
        if (context.get("building_type") or "").strip():
            parts.append(f"Тип будинку / конструкція: {context['building_type'].strip()}")
        if context.get("is_commercial"):
            parts.append("Комерційне призначення: так")
        hints = (context.get("hints") or "").strip()
        if hints:
            parts.append(f"Додаткові побажання автора оголошення: {hints}")

        facts = "\n".join(parts)
        prompt = f"""
Ти копірайтер оголошень нерухомості в Україні. За наведеними нижче ФАКТАМИ (без вигадування нових цифр і адрес)
напиши привабливий опис українською для сайту оголошень.

ФАКТИ:
{facts}

ВИМОГИ:
- 2–5 абзаців звичайного тексту (без Markdown-заголовків ##, без HTML, без списку «ID:»).
- Не додавай номер телефону, посилання на месенджери, вигадані документи чи юридичні гарантії.
- Якщо якихось даних немає у ФАКТАХ — не вигадуй їх; можна загально згадати переваги типу житла.
- Стиль: доброзичливо, професійно, для потенційного покупця чи орендаря.
"""
        response = self.model.generate_content(prompt)
        text = (response.text or "").strip()
        if not text:
            raise ValueError("Модель повернула порожній текст")
        return text

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

"""
Swagger Documentation for All Views
Додайте ці декоратори до відповідних views

ВАЖЛИВО: Це файл-референс з прикладами декораторів.
Скопіюйте потрібні декоратори до відповідних views.py файлів.

Використання:
1. Відкрийте потрібний view файл (users/views.py, properties/views.py, ai/views.py)
2. Додайте імпорт: from drf_spectacular.utils import extend_schema, OpenApiExample
3. Скопіюйте декоратор перед класом view
4. Перезапустіть сервер
"""

# ============ ПРИКЛАДИ ДЕКОРАТОРІВ ============

"""
# ============ USERS VIEWS ============

# LoginView - додайте цей декоратор перед class LoginView:
@extend_schema(
    tags=['Authentication'],
    summary='Вхід користувача',
    description='Отримання JWT токенів (access і refresh)',
    examples=[
        OpenApiExample(
            'Login Example',
            value={
                "username": "john_doe",
                "password": "SecurePassword123"
            }
        )
    ]
)

# LogoutView - додайте цей декоратор перед class LogoutView:
@extend_schema(
    tags=['Authentication'],
    summary='Вихід користувача',
    description='Додає refresh токен в blacklist',
    examples=[
        OpenApiExample(
            'Logout Example',
            value={
                "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
            }
        )
    ]
)

# UserProfileView - додайте цей декоратор перед class UserProfileView:
@extend_schema(
    tags=['Authentication'],
    summary='Профіль користувача',
    description='GET - отримання профілю, PATCH - оновлення профілю',
)

# ChangePasswordView - додайте цей декоратор перед class ChangePasswordView:
@extend_schema(
    tags=['Authentication'],
    summary='Зміна паролю',
    description='Зміна паролю авторизованого користувача',
    examples=[
        OpenApiExample(
            'Change Password Example',
            value={
                "old_password": "OldPassword123",
                "new_password": "NewPassword456",
                "new_password_confirm": "NewPassword456"
            }
        )
    ]
)

# ============ PROPERTIES VIEWS ============

# PropertyListView - додайте цей декоратор перед class PropertyListView:
@extend_schema(
    tags=['Properties'],
    summary='Список нерухомості',
    description='''
    Отримання списку об'єктів нерухомості з фільтрацією.
    
    Фільтри:
    - city: Місто
    - min_price / max_price: Діапазон цін
    - rooms_count: Кількість кімнат
    - realty_type: apartment / house
    - sale_type: sale / rent
    ''',
)

# PropertyDetailView - додайте цей декоратор перед class PropertyDetailView:
@extend_schema(
    tags=['Properties'],
    summary='Деталі об\'єкта',
    description='Отримання повної інформації про конкретний об\'єкт',
)

# ============ AI VIEWS ============

# ChatAssistantView - додайте цей декоратор перед class ChatAssistantView:
@extend_schema(
    tags=['AI Assistant'],
    summary='AI чат-асистент',
    description='''
    Розумний асистент для пошуку нерухомості.
    Розуміє природну мову українською та англійською.
    Користувач визначається автоматично з JWT токену.
    ''',
    examples=[
        OpenApiExample(
            'Chat Example 1',
            value={
                "message": "Хочу 2-кімнатну квартиру у Львові до 100000 доларів"
            }
        ),
        OpenApiExample(
            'Chat Example 2',
            value={
                "message": "Покажи мені недорогі варіанти в центрі"
            }
        )
    ]
)

# ExplainPropertyView - додайте цей декоратор перед class ExplainPropertyView:
# @extend_schema(
#     tags=['AI Assistant'],
#     summary='Пояснення об\'єкта',
#     description='AI генерує детальний опис об\'єкта з аналізом переваг',
#     examples=[
#         OpenApiExample(
#             'Explain Example',
#             value={
#                 "property_id": 1
#             }
#         )
#     ]
# )

# SemanticSearchView - додайте цей декоратор перед class SemanticSearchView:
# @extend_schema(
#     tags=['AI Assistant'],
#     summary='Семантичний пошук',
#     description='Пошук нерухомості за описом на природній мові',
#     examples=[
#         OpenApiExample(
#             'Search Example',
#             value={
#                 "query": "Затишна квартира для сім'ї з дітьми"
#             }
#         )
#     ]
# )

# ComparePropertiesView - додайте цей декоратор перед class ComparePropertiesView:
# @extend_schema(
#     tags=['AI Assistant'],
#     summary='Порівняння об\'єктів',
#     description='AI порівнює кілька об\'єктів та рекомендує найкращий',
#     examples=[
#         OpenApiExample(
#             'Compare Example',
#             value={
#                 "property_ids": [1, 2, 3]
#             }
#         )
#     ]
# )
"""
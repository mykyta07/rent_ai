#!/usr/bin/env python
"""
Скрипт для регенерування embeddings для об'єктів що їх не мають.
Пропускає об'єкти з існуючими embeddings щоб не витратити API квоту.

Використання:
  python clear_embeddings.py                    # Регенерує тільки відсутні
  python clear_embeddings.py --force-all        # Видалює старі та регенерує все
  python clear_embeddings.py --clear-invalid    # Видаляє embedding з невправильним розміром
"""
import os
import sys
import django

# Налаштовуємо Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from ai.models import PropertyEmbedding
from properties.models import Property
from ai.gemini_service import GeminiService

# Обробляємо аргументи
force_all = '--force-all' in sys.argv
clear_invalid = '--clear-invalid' in sys.argv

# Ініціалізуємо Gemini сервіс
gemini = GeminiService()

if force_all:
    print("🧹 РЕЖИМ: Видалення ВСІХ старих embeddings...")
    deleted_count, _ = PropertyEmbedding.objects.all().delete()
    print(f"✓ Видалено {deleted_count} старих embeddings\n")
elif clear_invalid:
    print("🧹 РЕЖИМ: Видалення embedding-ів з невправильним розміром...")
    # Визначаємо правильний розмір (за новою моделлю)
    test_embedding = gemini.generate_embedding("тест")
    expected_size = len(test_embedding)
    
    invalid_embeddings = PropertyEmbedding.objects.all()
    deleted_count = 0
    
    for emb in invalid_embeddings:
        if len(emb.embedding) != expected_size:
            emb.delete()
            deleted_count += 1
            print(f"✗ Видалено embedding для ID:{emb.property.id} (розмір: {len(emb.embedding)})")
    
    print(f"✓ Видалено {deleted_count} невалідних embeddings\n")
else:
    print("🔍 РЕЖИМ: Регенерування тільки відсутніх embeddings")
    print("   (Наявні embeddings будуть пропущені)\n")

print("\n🔄 Регенерування embeddings для об'єктів...")

# Знаходимо об'єкти без embeddings
from django.db.models import Q
properties_without_embeddings = Property.objects.filter(
    Q(embedding__isnull=True) | ~Q(id__in=PropertyEmbedding.objects.values_list('property_id', flat=True))
)

total_properties = properties_without_embeddings.count()
total_with_embeddings = Property.objects.count() - total_properties

print(f"📊 Статистика:")
print(f"   • Всього об'єктів: {Property.objects.count()}")
print(f"   • Уже мають embeddings: {total_with_embeddings}")
print(f"   • Потребують embeddings: {total_properties}")

if total_properties == 0:
    print("✅ Всі об'єкти вже мають embeddings, нічого робити не треба!")
    sys.exit(0)

success_count = 0
error_count = 0

for i, prop in enumerate(properties_without_embeddings, 1):
    try:
        location = prop.location if hasattr(prop, 'location') else None
        
        text_parts = [
            f"Назва: {prop.title}",
            f"Опис: {prop.description}",
            f"Тип угоди: {prop.get_sale_type_display()}",
            f"Кімнат: {prop.rooms_count}",
            f"Площа: {prop.total_area} м²",
        ]
        
        if location:
            text_parts.extend([
                f"Місто: {location.city}",
                f"Район: {location.district or ''}",
                f"Вулиця: {location.street or ''}",
            ])
        
        text = "\n".join(text_parts)
        
        # Генеруємо embedding
        embedding = gemini.generate_embedding(text)
        
        # Зберігаємо в БД
        PropertyEmbedding.objects.update_or_create(
            property=prop,
            defaults={
                'embedding': embedding,
                'model_name': gemini.embedding_model
            }
        )
        
        success_count += 1
        print(f"[{i}/{total_properties}] ✓ ID:{prop.id} - {prop.title[:40]}")
        
    except Exception as e:
        error_count += 1
        print(f"[{i}/{total_properties}] ✗ ID:{prop.id} - Помилка: {str(e)}")

print("\n" + "="*60)
print(f"✅ ГОТОВО!")
print(f"   • Успішно оброблено: {success_count}")
print(f"   • Помилок: {error_count}")
print(f"   • Всього мають embeddings: {PropertyEmbedding.objects.count()}")
print("="*60)

if error_count == 0:
    print("🎉 Все гаразд! Embeddings готові для використання.")
else:
    print(f"⚠️  Є {error_count} помилок. Запустіть скрипт повторно для повторної спроби.")
    print("\nДля видалення невалідних embeddings запустіть:")
    print("  python clear_embeddings.py --clear-invalid")


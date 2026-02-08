"""
Management command to generate embeddings for all properties
"""
from django.core.management.base import BaseCommand
from ai.gemini_service import GeminiService
from properties.models import Property
from ai.models import PropertyEmbedding


class Command(BaseCommand):
    help = 'Генерує embeddings для всіх об\'єктів нерухомості'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Перегенерувати embeddings навіть якщо вони вже існують'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Максимальна кількість об\'єктів для обробки'
        )

    def handle(self, *args, **options):
        force = options['force']
        limit = options['limit']
        
        self.stdout.write(self.style.NOTICE('🚀 Початок генерації embeddings...'))
        
        # Ініціалізуємо Gemini сервіс
        gemini = GeminiService()
        
        # Визначаємо які об'єкти обробляти
        if force:
            self.stdout.write(self.style.WARNING('⚠️  Режим --force: видаляю всі існуючі embeddings'))
            PropertyEmbedding.objects.all().delete()
            properties = Property.objects.all()
        else:
            # Тільки ті що не мають embeddings
            existing_ids = PropertyEmbedding.objects.values_list('property_id', flat=True)
            properties = Property.objects.exclude(id__in=existing_ids)
        
        if limit:
            properties = properties[:limit]
        
        total = properties.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('✅ Всі об\'єкти вже мають embeddings!'))
            return
        
        self.stdout.write(f'📊 Знайдено об\'єктів для обробки: {total}')
        self.stdout.write('')
        
        success_count = 0
        error_count = 0
        
        for i, prop in enumerate(properties, 1):
            try:
                location = prop.location if hasattr(prop, 'location') else None
                
                # Формуємо повний текст для embedding
                text_parts = [
                    prop.title,
                    prop.description,
                    f"Тип: {prop.get_realty_type_display()}",
                    f"Угода: {prop.get_sale_type_display()}",
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
                self.stdout.write(f'[{i}/{total}] Обробка ID:{prop.id}...', ending='')
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
                self.stdout.write(self.style.SUCCESS(' ✓'))
                self.stdout.write(f'    {prop.title[:60]}')
                
                # Прогрес
                if i % 10 == 0:
                    self.stdout.write(self.style.NOTICE(f'📈 Прогрес: {i}/{total} ({i/total*100:.1f}%)'))
                    self.stdout.write('')
                
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f' ✗ Помилка: {str(e)}'))
                continue
        
        # Підсумок
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'✅ Готово!'))
        self.stdout.write(f'📊 Успішно: {success_count}')
        if error_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠️  Помилок: {error_count}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Статистика
        total_embeddings = PropertyEmbedding.objects.count()
        total_properties = Property.objects.count()
        coverage = (total_embeddings / total_properties * 100) if total_properties > 0 else 0
        
        self.stdout.write('')
        self.stdout.write(f'📈 Покриття: {total_embeddings}/{total_properties} ({coverage:.1f}%)')
        
        if coverage < 100:
            missing = total_properties - total_embeddings
            self.stdout.write(
                self.style.WARNING(f'⚠️  Залишилось об\'єктів без embeddings: {missing}')
            )
            self.stdout.write(
                self.style.NOTICE('💡 Запустіть команду ще раз щоб обробити решту')
            )

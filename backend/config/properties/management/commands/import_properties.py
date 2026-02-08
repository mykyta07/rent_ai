import requests
import time
import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from properties.models import Property, PropertyPhoto, Location
from decimal import Decimal


class Command(BaseCommand):
    help = 'Імпорт нерухомості з DOM.RIA API (спочатку ID, потім деталі)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Кількість оголошень для імпорту'
        )
        parser.add_argument(
            '--cities',
            nargs='+',
            default=['Київ', 'Львів', 'Харків'],
            help='Міста для пошуку'
        )

    def handle(self, *args, **options):
        api_key = os.getenv('DOMRIA_API_KEY')
        if not api_key:
            self.stdout.write(self.style.ERROR('❌ API ключ не знайдено в .env'))
            return

        total_count = options['count']
        cities_to_search = options['cities']
        per_city = total_count // len(cities_to_search)

        self.stdout.write(self.style.SUCCESS(f'🔑 API Key: {api_key[:10]}...'))
        self.stdout.write(f'📊 Імпорт по {per_city} оголошень з кожного міста\n')

        # Конфігурація міст
        city_configs = {
            'Київ': {'state_id': 10, 'city_id': 10},
            'Львів': {'state_id': 14, 'city_id': 5},
            'Харків': {'state_id': 19, 'city_id': 1},
            'Одеса': {'state_id': 15, 'city_id': 1},
            'Дніпро': {'state_id': 11, 'city_id': 11},
            'Луцьк': {'state_id': 5, 'city_id': 1},
            'Житомир': {'state_id': 9, 'city_id': 1},
        }

        total_imported = 0

        for city_name in cities_to_search:
            if city_name not in city_configs:
                self.stdout.write(self.style.WARNING(f'⚠️  Невідоме місто: {city_name}'))
                continue

            city_config = city_configs[city_name]
            
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"🏙️  {city_name}")
            self.stdout.write(f"{'='*60}\n")

            # КРОК 1: Отримуємо список ID
            property_ids = self.get_property_ids(
                api_key,
                city_config,
                per_city
            )

            if not property_ids:
                self.stdout.write(self.style.WARNING(f'⚠️  Не знайдено оголошень для {city_name}\n'))
                continue

            self.stdout.write(f'📝 Знайдено {len(property_ids)} ID оголошень\n')

            # КРОК 2: Імпортуємо кожне оголошення за ID
            imported = 0
            for idx, realty_id in enumerate(property_ids, 1):
                success = self.import_property_by_id(
                    api_key,
                    realty_id,
                    city_name
                )

                if success:
                    imported += 1
                    total_imported += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✓ {idx}/{len(property_ids)}: ID {realty_id}'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠️  {idx}/{len(property_ids)}: ID {realty_id} - помилка'
                    ))

                # Затримка між запитами
                time.sleep(0.3)

            self.stdout.write(f'\n✅ Імпортовано {imported} оголошень з {city_name}')

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(self.style.SUCCESS(f'🎉 ЗАГАЛОМ ІМПОРТОВАНО: {total_imported} оголошень'))
        self.stdout.write(f"{'='*60}\n")

    def get_property_ids(self, api_key, city_config, limit):
        """
        КРОК 1: Отримує список ID оголошень через /search endpoint
        """
        all_ids = []
        page = 0
        max_pages = 10

        while len(all_ids) < limit and page < max_pages:
            try:
                url = 'https://developers.ria.com/dom/search'
                params = {
                    'api_key': api_key,
                    'category': 1,  # Квартири
                    'operation_type': 1,  # Продаж
                    'state_id': city_config['state_id'],
                    'city_id': city_config['city_id'],
                    'page': page,
                }

                self.stdout.write(f'  📄 Завантаження сторінки {page + 1}...', ending=' ')

                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 429:
                    self.stdout.write(self.style.ERROR('⚠️ Ліміт API'))
                    break

                if response.status_code != 200:
                    self.stdout.write(self.style.ERROR(f'✗ Помилка {response.status_code}'))
                    break

                data = response.json()
                items = data.get('items', [])

                if not items:
                    self.stdout.write('пусто')
                    break

                self.stdout.write(self.style.SUCCESS(f'✓ {len(items)} ID'))
                all_ids.extend(items[:limit - len(all_ids)])

                page += 1
                time.sleep(0.5)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Помилка: {e}'))
                break

        return all_ids[:limit]

    def import_property_by_id(self, api_key, realty_id, city_name):
        """
        КРОК 2: Отримує детальну інформацію про оголошення через /info endpoint
        """
        try:
            # Перевірка на дублікат
            if Property.objects.filter(description__contains=f'ID:{realty_id}').exists():
                return False

            url = f'https://developers.ria.com/dom/info/{realty_id}'
            params = {
                'api_key': api_key,
                'lang_id': 4  # Українська
            }

            response = requests.get(url, params=params, timeout=30)

            if response.status_code != 200:
                return False

            data = response.json()

            # Парсимо основні дані
            title = data.get('title', f'Нерухомість ID {realty_id}')
            description = data.get('description', '') + f'\n[DOM.RIA ID:{realty_id}]'

            # Ціна
            price_arr = data.get('priceArr', {})
            price = int(price_arr.get('1', 0) or price_arr.get('2', 0) or 0)

            if price == 0:
                return False

            # Характеристики
            rooms_count = data.get('rooms_count', 2)
            total_area = data.get('total_area')
            living_area = data.get('living_area')
            kitchen_area = data.get('kitchen_area')
            floor = data.get('floor')
            floors_count = data.get('floors_count')

            # Створюємо Property
            property_obj = Property.objects.create(
                title=title,
                description=description,
                price=price,
                rooms_count=rooms_count,
                total_area=self.safe_decimal(total_area),
                living_area=self.safe_decimal(living_area),
                kitchen_area=self.safe_decimal(kitchen_area),
                floor=floor,
                floors_count=floors_count,
                realty_type='apartment',
                sale_type='sale'
            )

            # Локація
            district = data.get('district_name', '')
            street = data.get('street_name', '')
            building = data.get('building_number', '')
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            Location.objects.create(
                property=property_obj,
                city=city_name,
                district=district,
                street=street,
                building_number=building,
                latitude=self.safe_decimal(latitude),
                longitude=self.safe_decimal(longitude)
            )

            # Фото
            photos = data.get('photos', {})
            if isinstance(photos, dict):
                photo_list = list(photos.values())[:8]
                for idx, photo_data in enumerate(photo_list):
                    if isinstance(photo_data, dict):
                        photo_id = photo_data.get('id') or photo_data.get('photo_id')
                        if photo_id:
                            photo_url = f"https://cdn.riastatic.com/photos/{photo_id}/640x480.webp"
                            PropertyPhoto.objects.create(
                                property=property_obj,
                                url=photo_url,
                                is_main=(idx == 0)
                            )

            return True

        except Exception as e:
            return False

    def safe_decimal(self, value):
        """Безпечне перетворення в Decimal"""
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except:
            return None

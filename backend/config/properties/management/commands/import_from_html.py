"""
Management command to import properties from saved DOM.RIA HTML file
"""
import re
import os
from pathlib import Path
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.conf import settings
from bs4 import BeautifulSoup
from properties.models import Property, Location, PropertyPhoto


class Command(BaseCommand):
    help = 'Import properties from saved DOM.RIA HTML file from html/ folder'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=False,
            default=None,
            help='Filename in html/ folder (e.g., page1.html). If not specified, imports from all HTML files'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of properties to import per file'
        )

    def handle(self, *args, **options):
        filename = options['file']
        limit = options['limit']
        
        # Get project root (parent of config folder)
        project_root = Path(settings.BASE_DIR).parent
        html_folder = project_root / 'html'
        
        # Create html folder if doesn't exist
        html_folder.mkdir(exist_ok=True)
        
        # If specific file is provided, process only that file
        if filename:
            html_file = html_folder / filename
            if not html_file.exists():
                self.stdout.write(self.style.ERROR(f'File not found: {html_file}'))
                self.stdout.write(f'Please place HTML files in: {html_folder}')
                
                # List available files
                html_files = list(html_folder.glob('*.html'))
                if html_files:
                    self.stdout.write('\nAvailable files:')
                    for f in html_files:
                        self.stdout.write(f'  - {f.name}')
                return
            
            files_to_process = [html_file]
        else:
            # Process all HTML files in the folder
            files_to_process = sorted(html_folder.glob('*.html'))
            
            if not files_to_process:
                self.stdout.write(self.style.WARNING(f'No HTML files found in: {html_folder}'))
                self.stdout.write(f'Please place HTML files in: {html_folder}')
                return
            
            self.stdout.write(self.style.SUCCESS(f'📁 Found {len(files_to_process)} HTML files to process'))
        
        # Statistics for all files
        total_imported = 0
        total_skipped = 0
        total_errors = 0
        
        # Process each file
        for html_file in files_to_process:
            self.stdout.write(self.style.SUCCESS(f'\n📄 Processing: {html_file.name}'))
            self.stdout.write('─' * 60)
            
            stats = self.process_file(html_file, limit)
            
            total_imported += stats['imported']
            total_skipped += stats['skipped']
            total_errors += stats['errors']
            
            self.stdout.write(self.style.SUCCESS(
                f'✅ {html_file.name}: {stats["imported"]} imported, {stats["skipped"]} skipped, {stats["errors"]} errors'
            ))
        
        # Final summary
        self.stdout.write('\n' + '═' * 60)
        self.stdout.write(self.style.SUCCESS(
            f'🎉 TOTAL: {total_imported} imported, {total_skipped} skipped, {total_errors} errors from {len(files_to_process)} file(s)'
        ))

    def process_file(self, html_file, limit):
        """Process a single HTML file and return statistics"""
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Find all property items
        property_items = soup.find_all('section', class_='realty-item')
        self.stdout.write(f'Found {len(property_items)} property items in HTML')
        
        imported = 0
        skipped = 0
        errors = 0
        
        for item in property_items:
            if limit and imported >= limit:
                break
            
            try:
                # Extract property URL and ID
                link = item.find('a', class_='realty-link')
                if not link or not link.get('href'):
                    continue
                
                url = link['href']
                # Extract ID from URL like: realty-prodaja-kvartira-lvov-...-33895849.html
                # or realty-arenda-kvartira-lvov-...-33895849.html
                id_match = re.search(r'-(\d+)\.html', url)
                if not id_match:
                    continue
                
                realty_id = id_match.group(1)
                
                # Визначаємо тип угоди з URL
                # URL формат: realty-prodaja-... або realty-arenda-...
                if 'arenda' in url or 'rent' in url.lower():
                    sale_type = 'rent'
                else:
                    sale_type = 'sale'
                
                # Check if already exists
                if Property.objects.filter(description__contains=f'DOM.RIA ID: {realty_id}').exists():
                    skipped += 1
                    continue
                
                # Extract price
                price_elem = item.find('b', class_='size22')
                if not price_elem:
                    continue
                
                price_text = price_elem.get_text(strip=True)
                price_data = self.parse_price(price_text)
                if not price_data:
                    continue
                
                price = price_data['price']
                currency = price_data['currency']
                
                # Extract title (street address)
                title_elem = item.find('a', class_='size22')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Extract location info
                city = self.extract_city(item)
                district = self.extract_district(item)
                street = self.extract_street(title)
                building_number = self.extract_building_number(title)
                
                # Extract characteristics
                chars = self.extract_characteristics(item)
                
                # Extract description
                description = self.extract_description(item, realty_id)
                
                # Extract photos
                photos = self.extract_photos(item)
                
                # Create Property
                property_obj = Property.objects.create(
                    title=title[:255],
                    description=description,
                    price=price,
                    currency=currency,
                    rooms_count=chars.get('rooms_count'),
                    total_area=chars.get('total_area'),
                    floor=chars.get('floor'),
                    floors_count=chars.get('floors_count'),
                    realty_type='apartment',  # Default to apartment
                    sale_type=sale_type  # Визначено з URL
                )
                
                # Create Location
                Location.objects.create(
                    property=property_obj,
                    city=city or 'Львів',
                    district=district,
                    street=street,
                    building_number=building_number
                )
                
                # Create Photos
                for idx, photo_url in enumerate(photos[:8]):
                    PropertyPhoto.objects.create(
                        property=property_obj,
                        url=photo_url,
                        is_main=(idx == 0)
                    )
                
                imported += 1
                sale_type_display = "🏠 ОРЕНДА" if sale_type == 'rent' else "💰 ПРОДАЖ"
                self.stdout.write(
                    self.style.SUCCESS(f'✓ {sale_type_display}: {title[:50]} - {price:,.0f}{currency}')
                )
                
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Error processing item: {str(e)}')
                )
                continue
        
        return {
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        }

    def parse_price(self, price_text):
        """Parse price and currency from text like '60 000 $' or '15 000 грн'"""
        try:
            # Визначаємо валюту
            if '$' in price_text or 'дол' in price_text.lower():
                currency = '$'
            elif 'грн' in price_text or '₴' in price_text:
                currency = 'грн'
            elif '€' in price_text or 'евро' in price_text.lower():
                currency = '€'
            else:
                currency = '$'  # За замовчуванням
            
            # Витягуємо число (видаляємо все крім цифр)
            price_clean = re.sub(r'[^\d]', '', price_text)
            if price_clean:
                return {
                    'price': Decimal(price_clean),
                    'currency': currency
                }
        except (ValueError, InvalidOperation):
            pass
        return None

    def extract_city(self, item):
        """Extract city from location span"""
        city_elem = item.find('span', class_='rCity')
        if city_elem:
            return city_elem.get_text(strip=True)
        return None

    def extract_district(self, item):
        """Extract district from location info"""
        # District is usually before city
        location_spans = item.find_all('span', class_='i-block')
        for span in location_spans:
            text = span.get_text(strip=True)
            # Check if it's not city and not empty
            if text and '·' not in text and not any(x in text for x in ['м²', 'кімнат', 'поверх']):
                # If it contains typical district names
                if any(word in text for word in ['ський', 'івський', 'ний', 'Центр', 'вул']):
                    continue
                return text
        return None

    def extract_street(self, title):
        """Extract street name from title like 'вул. Франка Івана, 15'"""
        # Remove building number
        street = re.sub(r',\s*\d+[а-я]?\s*$', '', title)
        # Remove 'вул.' prefix
        street = re.sub(r'^вул\.\s*', '', street)
        return street[:200] if street else None

    def extract_building_number(self, title):
        """Extract building number from title"""
        match = re.search(r',\s*(\d+[а-я]?)\s*$', title)
        if match:
            return match.group(1)
        return None

    def extract_characteristics(self, item):
        """Extract rooms, area, floor info"""
        result = {}
        
        chars_div = item.find('div', class_='realty-chars')
        if not chars_div:
            return result
        
        char_items = chars_div.find_all('div', class_='realty-char')
        
        for char in char_items:
            text = char.get_text(strip=True)
            
            # Rooms: "1 кімната", "2 кімнати", "3 кімнати"
            rooms_match = re.search(r'(\d+)\s*кімнат', text)
            if rooms_match:
                result['rooms_count'] = int(rooms_match.group(1))
                continue
            
            # Area: "48 м²", "65.5 м²"
            area_match = re.search(r'([\d.]+)\s*м²', text)
            if area_match:
                try:
                    result['total_area'] = Decimal(area_match.group(1))
                except (ValueError, InvalidOperation):
                    pass
                continue
            
            # Floor: "1 поверх з 4", "3 поверх з 9"
            floor_match = re.search(r'(\d+)\s*поверх\s*з\s*(\d+)', text)
            if floor_match:
                result['floor'] = int(floor_match.group(1))
                result['floors_count'] = int(floor_match.group(2))
                continue
        
        return result

    def extract_description(self, item, realty_id):
        """Extract full description text"""
        desc_div = item.find('div', class_='desc-hidden')
        if desc_div:
            desc_text = desc_div.get_text(strip=True)
            # Add ID marker for duplicate detection
            return f"DOM.RIA ID: {realty_id}\n\n{desc_text}"
        return f"DOM.RIA ID: {realty_id}"

    def extract_photos(self, item):
        """Extract photo URLs"""
        photos = []
        
        # Find main photo carousel
        photo_div = item.find('div', class_='realty-photo-rotate')
        if not photo_div:
            return photos
        
        # Get all picture elements
        pictures = photo_div.find_all('picture', class_='img')
        
        for picture in pictures:
            # Try to get webp source first
            source = picture.find('source', attrs={'type': 'image/webp'})
            if source and source.get('srcset'):
                url = source['srcset']
                # Clean URL - remove CDN path if needed
                if url.startswith('http'):
                    photos.append(url)
                    
        return photos

"""
Створює 5 демо-користувачів-авторів і призначає їм усі оголошення без owner (round-robin).

Запуск з каталогу проєкту Django (де manage.py):
  python manage.py assign_demo_authors

Опція:
  --dry-run   лише показати кількість оголошень без owner, без змін у БД
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from properties.models import Property

# Синхронізуйте з фронтом (PropertyDetailPage) — ті самі username.
DEMO_AUTHORS = [
    ("olena_petryk", "olena.petryk@demo.rentai.local", "Олена", "Петрик"),
    ("andriy_shevchenko", "andriy.shevchenko@demo.rentai.local", "Андрій", "Шевченко"),
    ("kateryna_bondar", "kateryna.bondar@demo.rentai.local", "Катерина", "Бондар"),
    ("dmytro_melnyk", "dmytro.melnyk@demo.rentai.local", "Дмитро", "Мельник"),
    ("solomiia_hrytsenko", "solomiia.hrytsenko@demo.rentai.local", "Соломія", "Гриценко"),
]

JOINED_DAYS_AGO = (520, 410, 300, 190, 95)


class Command(BaseCommand):
    help = "5 демо-авторів + owner для Property з owner=NULL"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Без змін у БД — лише кількість оголошень без власника",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        User = get_user_model()

        orphans = Property.objects.filter(owner__isnull=True).order_by("id")
        total = orphans.count()

        if dry:
            self.stdout.write(self.style.WARNING(f"DRY-RUN: оголошень без owner: {total}"))
            return

        authors = []
        for idx, (username, email, first_name, last_name) in enumerate(DEMO_AUTHORS):
            try:
                user = User.objects.get(username=username)
                user.email = email
                user.first_name = first_name
                user.last_name = last_name
                user.is_active = True
                user.save(update_fields=["email", "first_name", "last_name", "is_active"])
                self.stdout.write(f"  Оновлено: @{user.username} — {first_name} {last_name}")
            except User.DoesNotExist:
                user = User(
                    username=username,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True,
                    date_joined=timezone.now() - timedelta(days=JOINED_DAYS_AGO[idx]),
                )
                user.set_unusable_password()
                user.save()
                self.stdout.write(self.style.SUCCESS(f"  Створено: @{user.username} — {first_name} {last_name}"))
            authors.append(user)

        for i, prop in enumerate(orphans):
            prop.owner = authors[i % len(authors)]
            prop.save(update_fields=["owner"])

        self.stdout.write(self.style.SUCCESS(f"Призначено owner для {total} оголошень (round-robin)."))

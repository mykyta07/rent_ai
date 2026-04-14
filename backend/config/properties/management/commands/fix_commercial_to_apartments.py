"""
У БД усі записи з realty_type=commercial переписати на apartment
(за вашими даними це завжди квартири). is_commercial скидається в False.
"""
from django.core.management.base import BaseCommand

from properties.models import Property


class Command(BaseCommand):
    help = "realty_type: commercial → apartment для всіх відповідних Property."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Лише показати кількість записів без змін у БД.",
        )

    def handle(self, *args, **options):
        qs = Property.objects.filter(realty_type="commercial")
        n = qs.count()
        if options["dry_run"]:
            self.stdout.write(f"DRY-RUN: знайдено записів з commercial: {n}.")
            return
        updated = qs.update(realty_type="apartment", is_commercial=False)
        self.stdout.write(
            self.style.SUCCESS(
                f"Оновлено {updated} запис(ів): commercial → apartment, is_commercial=False."
            )
        )

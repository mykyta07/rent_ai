"""
Переписування realty_type без зовнішніх API.

- За замовчуванням: евристика з title/description (рядок URL: у описі, якщо є).
- З --from-html: зчитування збережених *.html (як import_from_html) і зіставлення з БД за DOM.RIA ID.
"""
from pathlib import Path

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand

from properties.domria_realty_type import (
    domria_listing_id_from_description,
    infer_realty_type,
    infer_realty_type_from_realty_item_section,
)
from properties.models import Property


class Command(BaseCommand):
    help = (
        "Перерахувати realty_type: за замовчуванням з тексту в БД; "
        "з --from-html — лише з локальних HTML (без мережі та API)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показати зміни без збереження в БД.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="У режимі з тексту: не більше N записів Property. У --from-html: ігнорується.",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Друкувати кожен оновлений id.",
        )
        parser.add_argument(
            "--from-html",
            action="store_true",
            help="Брати тип з локальних HTML у каталозі html/ (рекомендовано).",
        )
        parser.add_argument(
            "--html-folder",
            type=str,
            default=None,
            help="Каталог з *.html (за замовчуванням: <backend>/html).",
        )
        parser.add_argument(
            "--html-file",
            type=str,
            default=None,
            help="Один файл у html-folder (інакше обробляються усі *.html).",
        )

    def handle(self, *args, **options):
        if options["from_html"]:
            self._handle_from_html(options)
        else:
            self._handle_from_db_text(options)

    def _html_paths(self, options):
        base = Path(options["html_folder"]) if options["html_folder"] else Path(settings.BASE_DIR).parent / "html"
        if options["html_file"]:
            p = base / options["html_file"]
            if not p.is_file():
                self.stdout.write(self.style.ERROR(f"Файл не знайдено: {p}"))
                return []
            return [p]
        files = sorted(base.glob("*.html"))
        if not files:
            self.stdout.write(self.style.WARNING(f"Немає *.html у {base}"))
        return files

    def _handle_from_html(self, options):
        dry_run = options["dry_run"]
        verbose = options["verbose"]
        paths = self._html_paths(options)
        if not paths:
            return

        id_to_type: dict[str, str] = {}
        for path in paths:
            text = path.read_text(encoding="utf-8", errors="replace")
            soup = BeautifulSoup(text, "lxml")
            for section in soup.find_all("section", class_="realty-item"):
                rid, rt = infer_realty_type_from_realty_item_section(section)
                if rid:
                    id_to_type[rid] = rt

        self.stdout.write(f"З HTML отримано {len(id_to_type)} оголошень (унікальні id).")

        props_by_id: dict[str, list] = {}
        for prop in Property.objects.iterator(chunk_size=200):
            rid = domria_listing_id_from_description(prop.description)
            if not rid:
                continue
            props_by_id.setdefault(rid, []).append(prop)

        changed = 0
        unchanged = 0
        missing = 0
        batch = []
        batch_size = 200

        for rid, new_type in id_to_type.items():
            props = props_by_id.get(rid)
            if not props:
                missing += 1
                if verbose:
                    self.stdout.write(self.style.WARNING(f"  id оголошення {rid}: немає Property у БД"))
                continue
            for prop in props:
                if new_type == prop.realty_type:
                    unchanged += 1
                    continue
                old = prop.realty_type
                prop.realty_type = new_type
                changed += 1
                if verbose:
                    self.stdout.write(
                        f"  pk={prop.pk} DOM.RIA {rid}: {old!r} → {new_type!r} | {prop.title[:50]!r}"
                    )
                if not dry_run:
                    batch.append(prop)
                    if len(batch) >= batch_size:
                        Property.objects.bulk_update(batch, ["realty_type"])
                        batch.clear()

        if batch and not dry_run:
            Property.objects.bulk_update(batch, ["realty_type"])

        mode = "DRY-RUN (БД не змінювалась)" if dry_run else "Застосовано до БД"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode} (--from-html): оновлено {changed}, без змін {unchanged}, "
                f"id з HTML без запису в БД: {missing}."
            )
        )

    def _handle_from_db_text(self, options):
        dry_run = options["dry_run"]
        limit = options["limit"]
        verbose = options["verbose"]

        qs = Property.objects.all().order_by("id")
        if limit is not None:
            qs = qs[:limit]

        changed = 0
        unchanged = 0
        batch = []
        batch_size = 200

        for prop in qs.iterator(chunk_size=100):
            new_type = infer_realty_type(
                url="",
                title=prop.title,
                description=prop.description or "",
            )
            if new_type == prop.realty_type:
                unchanged += 1
                continue

            old = prop.realty_type
            prop.realty_type = new_type
            changed += 1

            if verbose:
                self.stdout.write(
                    f"  id={prop.pk}: {old!r} → {new_type!r} | {prop.title[:60]!r}"
                )

            if not dry_run:
                batch.append(prop)
                if len(batch) >= batch_size:
                    Property.objects.bulk_update(batch, ["realty_type"])
                    batch.clear()

        if batch and not dry_run:
            Property.objects.bulk_update(batch, ["realty_type"])

        mode = "DRY-RUN (БД не змінювалась)" if dry_run else "Застосовано до БД"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode} (за текстом у БД): оновлено {changed}, без змін {unchanged}."
            )
        )

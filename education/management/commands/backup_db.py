import shutil
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "SQLite nusgasyny we JSON dump-y backups/ papkasyna ýazýar."

    def handle(self, *args, **options):
        folder = Path(settings.BASE_DIR) / "backups"
        folder.mkdir(exist_ok=True)
        stamp = timezone.now().strftime("%Y%m%d-%H%M%S")
        src = Path(settings.DATABASES["default"]["NAME"])
        dest = folder / f"db-{stamp}.sqlite3"
        shutil.copy2(src, dest)
        json_path = folder / f"dump-{stamp}.json"
        with json_path.open("w", encoding="utf-8") as handle:
            call_command("dumpdata", "education", stdout=handle)
        self.stdout.write(self.style.SUCCESS(f"Ätiýaç: {dest}"))
        self.stdout.write(self.style.SUCCESS(f"Dump: {json_path}"))

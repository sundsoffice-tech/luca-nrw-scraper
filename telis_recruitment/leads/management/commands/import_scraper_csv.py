import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from leads.models import Lead
from leads.utils.csv_import import CSVImporter


class Command(BaseCommand):
    help = 'Importiert Leads aus einer Scraper-CSV-Datei (z.B. vertrieb_kontakte.csv)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'csv_path', 
            nargs='?',
            type=str, 
            help='Pfad zur CSV-Datei (optional, Standard: ../vertrieb_kontakte.csv)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Zeigt nur was importiert würde, ohne zu speichern'
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Aktualisiert existierende Leads auch wenn Score niedriger ist'
        )
    
    def handle(self, *args, **options):
        csv_path = options.get('csv_path')
        dry_run = options.get('dry_run', False)
        force_update = options.get('force_update', False)
        
        # Default path if not provided
        if not csv_path:
            from telis.config import CSV_IMPORT_DEFAULT_PATHS
            
            scraper_path = Path(settings.BASE_DIR).parent
            possible_paths = [scraper_path / path for path in CSV_IMPORT_DEFAULT_PATHS]
            
            for p in possible_paths:
                if p.exists():
                    csv_path = str(p)
                    break
            
            if not csv_path:
                raise CommandError(
                    'Keine CSV-Datei gefunden. Bitte Pfad angeben:\n'
                    '  python manage.py import_scraper_csv /pfad/zu/datei.csv\n\n'
                    'Gesuchte Standard-Pfade:\n' + 
                    '\n'.join(f'  - {p}' for p in possible_paths)
                )
        
        csv_path = Path(csv_path)
        if not csv_path.exists():
            raise CommandError(f'Datei nicht gefunden: {csv_path}')
        
        self.stdout.write(f'\n📂 Importiere aus: {csv_path}')
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  DRY RUN - Keine Änderungen werden gespeichert\n'))
        
        # Use the CSV Importer utility class
        importer = CSVImporter(dry_run=dry_run, force_update=force_update)
        
        try:
            stats = importer.import_from_file(csv_path)
            
            # Display summary
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(self.style.SUCCESS('✅ Import abgeschlossen:'))
            self.stdout.write(f'  🆕 Neu importiert: {stats["imported"]}')
            self.stdout.write(f'  🔄 Aktualisiert:   {stats["updated"]}')
            self.stdout.write(f'  ⏭️  Übersprungen:   {stats["skipped"]}')
            
            if stats["errors"]:
                self.stdout.write(self.style.ERROR(f'  ❌ Fehler:         {len(stats["errors"])}'))
                for error in stats["errors"][:5]:  # Show first 5 errors
                    self.stdout.write(self.style.ERROR(f'     {error}'))
                if len(stats["errors"]) > 5:
                    self.stdout.write(self.style.ERROR(f'     ... and {len(stats["errors"]) - 5} more'))
            
            self.stdout.write('=' * 50 + '\n')
            
        except FileNotFoundError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f'Fehler beim Import: {str(e)}')

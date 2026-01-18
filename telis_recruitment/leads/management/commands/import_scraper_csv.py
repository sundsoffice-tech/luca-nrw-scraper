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
            scraper_path = Path(settings.BASE_DIR).parent
            possible_paths = [
                scraper_path / 'vertrieb_kontakte.csv',
                scraper_path / 'leads.csv',
                scraper_path / 'export.csv',
                scraper_path / 'vertrieb_kontakte.xlsx',
            ]
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
        
        # Use the CSV importer utility
        importer = CSVImporter(dry_run=dry_run, force_update=force_update)
        
        try:
            stats = importer.import_from_file(str(csv_path))
            
            # Print summary
            self.stdout.write('\n' + '=' * 50)
            self.stdout.write(self.style.SUCCESS('✅ Import abgeschlossen:'))
            self.stdout.write(f'  🆕 Neu importiert: {stats["imported"]}')
            self.stdout.write(f'  🔄 Aktualisiert:   {stats["updated"]}')
            self.stdout.write(f'  ⏭️  Übersprungen:   {stats["skipped"]}')
            
            if stats['errors']:
                self.stdout.write(self.style.ERROR(f'  ❌ Fehler:         {len(stats["errors"])}'))
                self.stdout.write('\nFehlerdetails:')
                for error in stats['errors'][:10]:  # Show first 10 errors
                    self.stdout.write(self.style.ERROR(f'  {error}'))
                
                if len(stats['errors']) > 10:
                    self.stdout.write(
                        self.style.ERROR(f'  ... und {len(stats["errors"]) - 10} weitere Fehler')
                    )
                
                # Write full error report if available
                error_report = importer.get_error_report()
                if error_report and not dry_run:
                    error_file = csv_path.parent / f'import_errors_{csv_path.stem}.txt'
                    with open(error_file, 'w', encoding='utf-8') as f:
                        f.write(error_report)
                    self.stdout.write(f'\n📄 Vollständiger Fehlerbericht: {error_file}')
            
            self.stdout.write('=' * 50 + '\n')
        
        except FileNotFoundError as e:
            raise CommandError(str(e))
        except Exception as e:
            raise CommandError(f'Fehler beim Import: {str(e)}')

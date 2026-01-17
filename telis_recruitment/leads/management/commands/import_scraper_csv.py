import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from leads.models import Lead


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
        
        imported = 0
        updated = 0
        skipped = 0
        errors = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                # Detect delimiter
                sample = f.read(1024)
                f.seek(0)
                
                if ';' in sample and ',' not in sample:
                    delimiter = ';'
                else:
                    delimiter = ','
                
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = list(reader)
                
                self.stdout.write(f'📊 Gefunden: {len(rows)} Zeilen\n')
                
                with transaction.atomic():
                    for i, row in enumerate(rows, 1):
                        try:
                            result = self._process_row(row, i, dry_run, force_update)
                            if result == 'imported':
                                imported += 1
                            elif result == 'updated':
                                updated += 1
                            else:
                                skipped += 1
                        except Exception as e:
                            errors.append(f'Zeile {i}: {str(e)}')
                            self.stdout.write(self.style.ERROR(f'  ❌ [{i}] FEHLER: {str(e)}'))
                    
                    if dry_run:
                        # Rollback bei dry run
                        transaction.set_rollback(True)
        
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(csv_path, 'r', encoding='latin-1') as f:
                    # Detect delimiter
                    sample = f.read(1024)
                    f.seek(0)
                    
                    if ';' in sample and ',' not in sample:
                        delimiter = ';'
                    else:
                        delimiter = ','
                    
                    reader = csv.DictReader(f, delimiter=delimiter)
                    rows = list(reader)
                    self.stdout.write(self.style.WARNING('📝 Datei mit Latin-1 Encoding gelesen'))
                    self.stdout.write(f'📊 Gefunden: {len(rows)} Zeilen\n')
                    
                    with transaction.atomic():
                        for i, row in enumerate(rows, 1):
                            try:
                                result = self._process_row(row, i, dry_run, force_update)
                                if result == 'imported':
                                    imported += 1
                                elif result == 'updated':
                                    updated += 1
                                else:
                                    skipped += 1
                            except Exception as e:
                                errors.append(f'Zeile {i}: {str(e)}')
                                self.stdout.write(self.style.ERROR(f'  ❌ [{i}] FEHLER: {str(e)}'))
                        
                        if dry_run:
                            # Rollback bei dry run
                            transaction.set_rollback(True)
            except Exception as e:
                raise CommandError(f'Fehler beim Lesen der Datei: {e}')
        
        # Zusammenfassung
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('✅ Import abgeschlossen:'))
        self.stdout.write(f'  🆕 Neu importiert: {imported}')
        self.stdout.write(f'  🔄 Aktualisiert:   {updated}')
        self.stdout.write(f'  ⏭️  Übersprungen:   {skipped}')
        if errors:
            self.stdout.write(self.style.ERROR(f'  ❌ Fehler:         {len(errors)}'))
        self.stdout.write('=' * 50 + '\n')
    
    def _process_row(self, row, index, dry_run, force_update):
        """Verarbeitet eine einzelne CSV-Zeile"""
        
        # Feldnamen-Mapping (Scraper-Felder -> Django-Felder)
        email = (row.get('email') or row.get('Email') or row.get('E-Mail') or '').strip() or None
        telefon = (row.get('telefon') or row.get('Telefon') or row.get('phone') or '').strip() or None
        name = (row.get('name') or row.get('Name') or 'Unbekannt').strip()
        
        if not email and not telefon:
            return 'skipped'
        
        # Score parsen
        try:
            score_raw = row.get('score') or row.get('Score') or row.get('quality_score') or '50'
            score = int(score_raw) if score_raw else 50
            score = max(0, min(100, score))  # Clamp 0-100
        except (ValueError, TypeError):
            score = 50
        
        # Deduplizierung
        existing = None
        if email:
            existing = Lead.objects.filter(email=email).first()
        if not existing and telefon:
            existing = Lead.objects.filter(telefon=telefon).first()
        
        if existing:
            if force_update or score > existing.quality_score:
                if not dry_run:
                    existing.quality_score = score
                    # Update other fields if better data
                    if not existing.company and row.get('company_name'):
                        existing.company = row.get('company_name')[:255]
                    if not existing.role:
                        role = (row.get('rolle') or row.get('position') or row.get('Position') or '')
                        if role:
                            existing.role = role[:255]
                    if not existing.location:
                        location = (row.get('region') or row.get('standort') or row.get('Standort') or '')
                        if location:
                            existing.location = location[:255]
                    existing.save()
                self.stdout.write(self.style.WARNING(
                    f'  🔄 [{index}] UPDATE: {name} (Score: {existing.quality_score} → {score})'
                ))
                return 'updated'
            else:
                return 'skipped'
        else:
            # Lead-Type mapping
            lead_type_raw = row.get('lead_type') or row.get('Lead-Typ') or ''
            if lead_type_raw in dict(Lead.LeadType.choices):
                lead_type = lead_type_raw
            else:
                lead_type = Lead.LeadType.UNKNOWN
            
            if not dry_run:
                Lead.objects.create(
                    name=name[:255],
                    email=email,
                    telefon=telefon,
                    source=Lead.Source.SCRAPER,
                    source_url=(row.get('quelle') or row.get('source_url') or '')[:200] or None,
                    quality_score=score,
                    lead_type=lead_type,
                    company=(row.get('company_name') or row.get('firma') or row.get('Firma') or '')[:255] or None,
                    role=(row.get('rolle') or row.get('position') or row.get('Position') or '')[:255] or None,
                    location=(row.get('region') or row.get('standort') or row.get('Standort') or '')[:255] or None,
                    linkedin_url=row.get('social_profile_url') if 'linkedin' in (row.get('social_profile_url') or '').lower() else None,
                    xing_url=row.get('social_profile_url') if 'xing' in (row.get('social_profile_url') or '').lower() else None,
                )
            
            self.stdout.write(self.style.SUCCESS(
                f'  🆕 [{index}] NEU: {name} ({email or telefon}) [Score: {score}]'
            ))
            return 'imported'

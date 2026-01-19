"""
Management command to import leads from scraper.db SQLite database.

Usage:
    python manage.py import_scraper_db
    python manage.py import_scraper_db --db /path/to/scraper.db
    python manage.py import_scraper_db --watch --interval 60
    python manage.py import_scraper_db --dry-run
    python manage.py import_scraper_db --force
"""
import sqlite3
import time
import json
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from leads.models import Lead, SyncStatus
from leads.field_mapping import (
    SCRAPER_TO_DJANGO_MAPPING,
    JSON_ARRAY_FIELDS,
    is_json_field,
    is_integer_field,
    is_url_field
)


class Command(BaseCommand):
    help = 'Importiert Leads direkt aus der scraper.db SQLite-Datenbank ins Django-System'
    
    # Lead type mapping from scraper.db to Django Lead model
    LEAD_TYPE_MAPPING = {
        'active_salesperson': Lead.LeadType.ACTIVE_SALESPERSON,
        'team_member': Lead.LeadType.TEAM_MEMBER,
        'freelancer': Lead.LeadType.FREELANCER,
        'hr_contact': Lead.LeadType.HR_CONTACT,
        'candidate': Lead.LeadType.CANDIDATE,
        'talent_hunt': Lead.LeadType.TALENT_HUNT,
        'recruiter': Lead.LeadType.RECRUITER,
        'job_ad': Lead.LeadType.JOB_AD,
        'company': Lead.LeadType.COMPANY,
        'individual': Lead.LeadType.INDIVIDUAL,
    }
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--db',
            type=str,
            help='Path to scraper.db (default: ../scraper.db relative to telis_recruitment)'
        )
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Continuous watch mode - imports new leads every interval seconds'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=60,
            help='Interval in seconds for watch mode (default: 60)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be imported without saving'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force import all leads, ignoring last sync timestamp'
        )
    
    def handle(self, *args, **options):
        db_path = options.get('db')
        watch_mode = options.get('watch', False)
        interval = options.get('interval', 60)
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        
        # Determine database path
        if not db_path:
            # Default: ../scraper.db relative to telis_recruitment directory
            scraper_path = Path(settings.BASE_DIR).parent
            db_path = scraper_path / 'scraper.db'
            
            # Fallback to other possible names
            if not db_path.exists():
                alternatives = [
                    scraper_path / 'craper.db',  # Typo in actual filename
                    scraper_path / 'leads.db',
                ]
                for alt in alternatives:
                    if alt.exists():
                        db_path = alt
                        break
        else:
            db_path = Path(db_path)
        
        if not db_path.exists():
            raise CommandError(
                f'Scraper-Datenbank nicht gefunden: {db_path}\n'
                f'Bitte prüfen Sie den Pfad oder verwenden Sie --db /pfad/zu/scraper.db'
            )
        
        self.stdout.write(f'\n📂 Scraper-Datenbank: {db_path}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️  DRY RUN - Keine Änderungen werden gespeichert\n'))
        
        if watch_mode:
            self.stdout.write(
                self.style.SUCCESS(
                    f'👁️  Watch-Modus aktiviert (Interval: {interval}s)\n'
                    f'   Drücken Sie Ctrl+C zum Beenden\n'
                )
            )
            try:
                while True:
                    self._import_leads(db_path, dry_run, force)
                    self.stdout.write(
                        self.style.SUCCESS(f'\n⏰ Warte {interval} Sekunden bis zum nächsten Import...\n')
                    )
                    time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('\n\n⛔ Watch-Modus beendet\n'))
        else:
            self._import_leads(db_path, dry_run, force)
    
    def _import_leads(self, db_path, dry_run, force):
        """Import leads from scraper.db"""
        
        imported = 0
        updated = 0
        skipped = 0
        errors = []
        
        try:
            # Connect to scraper database
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            cursor = conn.cursor()
            
            # Get last sync status
            sync_status = None
            last_lead_id = 0
            
            if not force:
                try:
                    sync_status = SyncStatus.objects.get(source='scraper_db')
                    last_lead_id = sync_status.last_lead_id
                    self.stdout.write(
                        f'📊 Letzter Sync: {sync_status.last_sync_at.strftime("%Y-%m-%d %H:%M:%S")} '
                        f'(Lead-ID: {last_lead_id})\n'
                    )
                except SyncStatus.DoesNotExist:
                    self.stdout.write('📊 Erster Import - alle Leads werden importiert\n')
            else:
                self.stdout.write('📊 Force-Modus: Alle Leads werden neu geprüft\n')
            
            # Query leads from scraper.db (only new ones if incremental)
            # First check what columns exist
            cursor.execute("PRAGMA table_info(leads)")
            available_columns = [row[1] for row in cursor.fetchall()]
            
            # Build dynamic column list based on available columns
            columns_to_select = []
            for col in ['id', 'name', 'rolle', 'email', 'telefon', 'quelle', 'score', 
                       'tags', 'region', 'role_guess', 'lead_type', 'company_name', 
                       'location_specific', 'confidence_score', 'social_profile_url', 
                       'last_updated', 'phone_type', 'whatsapp_link', 'ai_category',
                       'ai_summary', 'opening_line', 'skills', 'availability',
                       'candidate_status', 'current_status', 'mobility', 'salary_hint',
                       'commission_hint', 'company_size', 'hiring_volume', 'industry',
                       'data_quality', 'private_address', 'profile_url', 'cv_url',
                       'contact_preference', 'recency_indicator', 'experience_years',
                       'linkedin_url', 'xing_url', 'location']:
                if col in available_columns:
                    columns_to_select.append(col)
            
            query = f"""
                SELECT {', '.join(columns_to_select)}
                FROM leads
                WHERE id > ?
                ORDER BY id ASC
            """
            
            cursor.execute(query, (last_lead_id,))
            rows = cursor.fetchall()
            
            self.stdout.write(f'📋 Gefundene neue Leads: {len(rows)}\n')
            
            if len(rows) == 0:
                self.stdout.write(self.style.SUCCESS('✅ Keine neuen Leads zum Importieren\n'))
                conn.close()
                return
            
            max_lead_id = last_lead_id
            
            with transaction.atomic():
                for row in rows:
                    try:
                        result = self._process_lead(dict(row), dry_run)
                        
                        if result == 'imported':
                            imported += 1
                        elif result == 'updated':
                            updated += 1
                        else:
                            skipped += 1
                        
                        # Track maximum lead ID
                        if row['id'] > max_lead_id:
                            max_lead_id = row['id']
                            
                    except Exception as e:
                        errors.append(f"Lead ID {row['id']}: {str(e)}")
                        self.stdout.write(
                            self.style.ERROR(f'  ❌ Lead ID {row["id"]}: {str(e)}')
                        )
                
                # Update sync status
                if not dry_run and (imported > 0 or updated > 0):
                    try:
                        sync_status = SyncStatus.objects.get(source='scraper_db')
                        sync_status.last_sync_at = timezone.now()
                        sync_status.last_lead_id = max_lead_id
                        sync_status.leads_imported += imported
                        sync_status.leads_updated += updated
                        sync_status.leads_skipped += skipped
                        sync_status.save()
                    except SyncStatus.DoesNotExist:
                        SyncStatus.objects.create(
                            source='scraper_db',
                            last_sync_at=timezone.now(),
                            last_lead_id=max_lead_id,
                            leads_imported=imported,
                            leads_updated=updated,
                            leads_skipped=skipped
                        )
                
                if dry_run:
                    # Rollback in dry run mode
                    transaction.set_rollback(True)
            
            conn.close()
            
        except sqlite3.Error as e:
            raise CommandError(f'Datenbankfehler: {e}')
        
        # Summary
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('✅ Import abgeschlossen:'))
        self.stdout.write(f'  🆕 Neu importiert: {imported}')
        self.stdout.write(f'  🔄 Aktualisiert:   {updated}')
        self.stdout.write(f'  ⏭️  Übersprungen:   {skipped}')
        if errors:
            self.stdout.write(self.style.ERROR(f'  ❌ Fehler:         {len(errors)}'))
            if len(errors) <= 5:
                for error in errors:
                    self.stdout.write(self.style.ERROR(f'     {error}'))
        self.stdout.write('=' * 50 + '\n')
    
    def _clean_field(self, value):
        """Helper to clean and normalize field values"""
        if not value:
            return None
        cleaned = str(value).strip()
        return cleaned if cleaned else None
    
    def _parse_json_field(self, value):
        """Parse JSON field from scraper.db"""
        if not value:
            return None
        if isinstance(value, (list, dict)):
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            # If it's a string that looks like a comma-separated list
            if isinstance(value, str) and ',' in value:
                return [item.strip() for item in value.split(',') if item.strip()]
            return None
    
    def _parse_integer_field(self, value):
        """Parse integer field from scraper.db"""
        if value is None or value == '':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _process_lead(self, row, dry_run):
        """Process a single lead from scraper.db"""
        
        # Extract and clean core fields
        email = self._clean_field(row.get('email'))
        telefon = self._clean_field(row.get('telefon'))
        name = self._clean_field(row.get('name')) or 'Unbekannt'
        
        # Skip if no contact info
        if not email and not telefon:
            return 'skipped'
        
        # Parse score
        score = self._parse_integer_field(row.get('score')) or 50
        score = max(0, min(100, score))  # Clamp to 0-100
        
        # Map lead type
        lead_type_raw = (row.get('lead_type') or '').lower()
        lead_type = self.LEAD_TYPE_MAPPING.get(lead_type_raw, Lead.LeadType.UNKNOWN)
        
        # Build field data dict using field mapping
        field_data = {}
        
        for scraper_field, django_field in SCRAPER_TO_DJANGO_MAPPING.items():
            if scraper_field not in row.keys():
                continue
                
            value = row.get(scraper_field)
            if value is None or value == '':
                continue
            
            # Parse based on field type
            if is_json_field(django_field):
                parsed_value = self._parse_json_field(value)
            elif is_integer_field(django_field):
                parsed_value = self._parse_integer_field(value)
            else:
                parsed_value = self._clean_field(value)
            
            if parsed_value is not None:
                field_data[django_field] = parsed_value
        
        # Handle special cases
        # Extract role (prefer role_guess over rolle)
        if 'role' not in field_data:
            role = self._clean_field(row.get('role_guess') or row.get('rolle'))
            if role:
                field_data['role'] = role
        
        # Extract location (prefer location_specific over region, then location)
        if 'location' not in field_data:
            location = self._clean_field(
                row.get('location_specific') or row.get('region') or row.get('location')
            )
            if location:
                field_data['location'] = location
        
        # Handle social profile URL splitting
        social_profile_url = self._clean_field(row.get('social_profile_url'))
        if social_profile_url:
            if 'linkedin' in social_profile_url.lower():
                field_data['linkedin_url'] = social_profile_url
            elif 'xing' in social_profile_url.lower():
                field_data['xing_url'] = social_profile_url
            # Also store in profile_url if not set
            if 'profile_url' not in field_data:
                field_data['profile_url'] = social_profile_url
        
        # Override with explicit linkedin/xing URLs if present
        if row.get('linkedin_url'):
            field_data['linkedin_url'] = self._clean_field(row.get('linkedin_url'))
        if row.get('xing_url'):
            field_data['xing_url'] = self._clean_field(row.get('xing_url'))
        
        # Check for existing lead (deduplication)
        existing = None
        if email:
            existing = Lead.objects.filter(email=email).first()
        if not existing and telefon:
            existing = Lead.objects.filter(telefon=telefon).first()
        
        if existing:
            # Update if score is higher or additional fields are available
            should_update = False
            
            if score > existing.quality_score:
                should_update = True
                existing.quality_score = score
            
            # Update empty fields with new data
            for django_field, value in field_data.items():
                # Skip fields that shouldn't be in the model
                if not hasattr(existing, django_field):
                    continue
                
                current_value = getattr(existing, django_field, None)
                
                # Update if current field is empty and we have new data
                if not current_value and value:
                    # Truncate string fields to max length
                    if isinstance(value, str) and hasattr(Lead._meta.get_field(django_field), 'max_length'):
                        max_length = Lead._meta.get_field(django_field).max_length
                        if max_length:
                            value = value[:max_length]
                    
                    setattr(existing, django_field, value)
                    should_update = True
            
            if lead_type != Lead.LeadType.UNKNOWN and existing.lead_type == Lead.LeadType.UNKNOWN:
                existing.lead_type = lead_type
                should_update = True
            
            if should_update and not dry_run:
                existing.save()
                self.stdout.write(
                    self.style.WARNING(
                        f'  🔄 UPDATE: {name} ({email or telefon}) [Score: {score}]'
                    )
                )
                return 'updated'
            else:
                return 'skipped'
        else:
            # Create new lead
            lead_data = {
                'name': name[:255],
                'email': email,
                'telefon': telefon,
                'source': Lead.Source.SCRAPER,
                'quality_score': score,
                'lead_type': lead_type,
            }
            
            # Add all mapped fields
            for django_field, value in field_data.items():
                # Skip fields that shouldn't be in the model
                if not hasattr(Lead, django_field):
                    continue
                
                # Truncate string fields to max length
                if isinstance(value, str):
                    try:
                        field = Lead._meta.get_field(django_field)
                        if hasattr(field, 'max_length') and field.max_length:
                            value = value[:field.max_length]
                    except:
                        pass
                
                lead_data[django_field] = value
            
            if not dry_run:
                Lead.objects.create(**lead_data)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'  🆕 NEU: {name} ({email or telefon}) [Score: {score}, Typ: {lead_type}]'
                )
            )
            return 'imported'

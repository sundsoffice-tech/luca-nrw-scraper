# -*- coding: utf-8 -*-
import os
import sys
import django
from django.apps import apps
from pathlib import Path

# Dynamically determine paths
repo_root = Path(__file__).resolve().parent
telis_root = repo_root / 'telis_recruitment'

os.chdir(str(telis_root))
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(telis_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telis.settings')
django.setup()

ScraperRun = apps.get_model('scraper_control', 'ScraperRun')
Lead = apps.get_model('leads', 'Lead')

print('=== LETZTE 5 RUNS ===')
for run in ScraperRun.objects.order_by('-started_at')[:5]:
    industry = run.parameters_snapshot.get('industry', '? ') if run.parameters_snapshot else '?'
    print(f"Run #{run.id}: {run.status} | Industry: {industry} | Leads: {run.leads_accepted}/{run.links_checked}")

print('\n=== LETZTE 10 LEADS ===')
for lead in Lead.objects.filter(source__icontains='scraper').order_by('-created_at')[:10]:
    name = (lead.company_name or '?')[:40].ljust(40)
    print(f"{name} | Score:  {lead.score or 0}")

print('\n=== LEAD STATS ===')
total = Lead.objects.filter(source__icontains='scraper').count()
with_email = Lead.objects.filter(source__icontains='scraper', email__isnull=False).exclude(email='').count()
with_phone = Lead.objects.filter(source__icontains='scraper', phone__isnull=False).exclude(phone='').count()
high_score = Lead.objects.filter(source__icontains='scraper', score__gte=70).count()
print(f"Total: {total}")
print(f"Mit Email: {with_email}")
print(f"Mit Telefon: {with_phone}")
print(f"Score >= 70: {high_score}")
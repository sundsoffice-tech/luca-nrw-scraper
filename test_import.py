print('Step 1: Import config.. .')
from luca_scraper.config import DATABASE_BACKEND
print(f'  DATABASE_BACKEND = {DATABASE_BACKEND}')

print('Step 2: Import repository...')
from luca_scraper import repository
print(f'  start_scraper_run_sqlite exists: {hasattr(repository, "start_scraper_run_sqlite")}')

print('Step 3: Import db_router...')
from luca_scraper import db_router
print(f'  start_scraper_run exists: {hasattr(db_router, "start_scraper_run")}')
print(f'  start_scraper_run = {getattr(db_router, "start_scraper_run", "NOT FOUND")}')

print('Step 4: Direct import...')
from luca_scraper.db_router import start_scraper_run
print(f'  SUCCESS: {start_scraper_run}')

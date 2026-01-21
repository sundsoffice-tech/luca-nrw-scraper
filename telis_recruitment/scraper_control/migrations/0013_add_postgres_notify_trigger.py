# Generated migration for PostgreSQL LISTEN/NOTIFY support

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scraper_control', '0012_urlseen_querydone'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Create function to send notification on new log entry
                CREATE OR REPLACE FUNCTION notify_log_insert()
                RETURNS trigger AS $$
                DECLARE
                    payload TEXT;
                BEGIN
                    -- Build JSON payload with log details
                    payload := json_build_object(
                        'id', NEW.id,
                        'run_id', NEW.run_id,
                        'level', NEW.level,
                        'message', LEFT(NEW.message, 1000),  -- Limit message to avoid 8KB limit
                        'portal', NEW.portal,
                        'created_at', to_char(NEW.created_at, 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"')
                    )::TEXT;
                    
                    -- Send notification on log_updates channel
                    PERFORM pg_notify('log_updates', payload);
                    
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                -- Create trigger that fires after INSERT on ScraperLog
                DROP TRIGGER IF EXISTS scraperlog_notify_trigger ON scraper_control_scraperlog;
                CREATE TRIGGER scraperlog_notify_trigger
                    AFTER INSERT ON scraper_control_scraperlog
                    FOR EACH ROW
                    EXECUTE FUNCTION notify_log_insert();
            """,
            reverse_sql="""
                -- Drop trigger and function
                DROP TRIGGER IF EXISTS scraperlog_notify_trigger ON scraper_control_scraperlog;
                DROP FUNCTION IF EXISTS notify_log_insert();
            """
        ),
    ]

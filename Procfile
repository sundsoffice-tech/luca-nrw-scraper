web: cd telis_recruitment && gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 120 telis.wsgi:application
release: cd telis_recruitment && python manage.py migrate --noinput

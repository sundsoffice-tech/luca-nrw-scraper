import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure Django for pytest-django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telis_recruitment.telis.settings')

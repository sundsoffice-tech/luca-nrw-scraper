# Contributing to Telis Recruitment System

Thank you for your interest in contributing to the Telis Recruitment System! This document provides guidelines and instructions for developers.

## Table of Contents
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

## Development Setup

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git
- Virtual environment tool (venv)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/sundsoffice-tech/luca-nrw-scraper.git
   cd luca-nrw-scraper
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Django dependencies**
   ```bash
   cd telis_recruitment
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## Code Style Guidelines

### Python Code Style

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line Length**: Maximum 120 characters
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Prefer single quotes for strings unless double quotes improve readability
- **Imports**: Group imports in the following order:
  1. Standard library imports
  2. Related third party imports
  3. Local application imports

### Django Specific Guidelines

- **Models**: 
  - Use verbose_name for all fields
  - Add help_text for complex fields
  - Define __str__ methods for all models
  - Use choices for enum-like fields

- **Views**:
  - Keep views thin, move business logic to models or utilities
  - Use class-based views where appropriate
  - Add docstrings explaining the purpose and parameters

- **Naming Conventions**:
  - Models: Singular, PascalCase (e.g., `Lead`, `CallLog`)
  - Views: snake_case (e.g., `import_csv`, `opt_in`)
  - URLs: kebab-case (e.g., `import-csv`, `opt-in`)

### Documentation

- Add docstrings to all functions, classes, and modules
- Use Google-style docstrings:
  ```python
  def function_name(param1: str, param2: int) -> bool:
      """
      Brief description of the function.
      
      Longer description if needed, explaining what the function does,
      any important details, and edge cases.
      
      Args:
          param1: Description of param1
          param2: Description of param2
          
      Returns:
          Description of return value
          
      Raises:
          ValueError: When param1 is empty
      """
  ```

## Testing

### Running Tests

Run all tests:
```bash
cd telis_recruitment
python manage.py test
```

Run specific test module:
```bash
python manage.py test leads.tests.LeadModelTest
```

Run with verbosity:
```bash
python manage.py test --verbosity=2
```

### Writing Tests

- **Location**: Tests go in `leads/tests.py`
- **Naming**: Test classes should end with `Test`, test methods should start with `test_`
- **Structure**: Use `setUp()` and `tearDown()` for test fixtures
- **Coverage**: Aim for high test coverage, especially for:
  - Model methods and properties
  - API endpoints
  - Business logic
  - Edge cases and error handling

Example test structure:
```python
class MyFeatureTest(TestCase):
    """Tests for MyFeature functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='test', password='test')
        
    def test_feature_works_correctly(self):
        """Test that feature behaves as expected"""
        result = my_feature()
        self.assertEqual(result, expected_value)
    
    def test_feature_handles_edge_case(self):
        """Test edge case handling"""
        with self.assertRaises(ValueError):
            my_feature(invalid_input)
```

### Test Database

Tests use a separate test database. Django automatically creates and destroys it for each test run.

## Pull Request Process

### Before Submitting

1. **Update your branch**
   ```bash
   git checkout main
   git pull origin main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run tests**
   ```bash
   python manage.py test
   ```

3. **Run linting**
   ```bash
   flake8 telis_recruitment --count --select=E9,F63,F7,F82 --show-source --statistics
   ```

4. **Check for migration issues**
   ```bash
   python manage.py makemigrations --check --dry-run
   ```

### Submitting a Pull Request

1. **Create a descriptive branch name**
   - Use format: `feature/description` or `fix/description`
   - Example: `feature/add-rate-limiting` or `fix/csv-import-encoding`

2. **Write a clear PR description**
   - What problem does this PR solve?
   - What changes were made?
   - How has this been tested?
   - Any breaking changes?

3. **PR Checklist**
   - [ ] Code follows style guidelines
   - [ ] Tests pass locally
   - [ ] New tests added for new functionality
   - [ ] Documentation updated if needed
   - [ ] No console warnings or errors
   - [ ] Migrations are included (if model changes)

### Code Review Process

1. At least one approval required
2. All CI checks must pass
3. No merge conflicts
4. Address all review comments

## Project Structure

```
telis_recruitment/
├── leads/                      # Main app for lead management
│   ├── management/commands/    # Django management commands
│   ├── migrations/            # Database migrations
│   ├── services/              # Business logic services
│   ├── utils/                 # Utility functions and classes
│   ├── admin.py               # Django admin configuration
│   ├── models.py              # Database models
│   ├── serializers.py         # REST API serializers
│   ├── tests.py               # Test cases
│   ├── urls.py                # URL routing
│   └── views.py               # View functions and classes
├── telis/                     # Project settings
│   ├── config.py              # Centralized configuration
│   ├── settings.py            # Django settings
│   └── urls.py                # Root URL configuration
├── templates/                 # HTML templates
│   ├── crm/                   # CRM interface templates
│   ├── landing/               # Landing page templates
│   └── phone/                 # Phone dashboard templates
├── static/                    # Static files (CSS, JS, images)
├── requirements.txt           # Python dependencies
└── manage.py                  # Django management script
```

## Common Tasks

### Adding a New Model

1. Define model in `leads/models.py`
2. Create migration: `python manage.py makemigrations`
3. Apply migration: `python manage.py migrate`
4. Add to admin: Update `leads/admin.py`
5. Write tests: Add to `leads/tests.py`

### Adding a New API Endpoint

1. Define view function/class in `leads/views.py` or `leads/views_*.py`
2. Add URL pattern to `leads/urls.py`
3. Add serializer if needed in `leads/serializers.py`
4. Write tests in `leads/tests.py`
5. Document in API documentation

### Adding a Management Command

1. Create file in `leads/management/commands/`
2. Inherit from `BaseCommand`
3. Implement `handle()` method
4. Add tests
5. Document usage in command docstring

## Getting Help

- **Issues**: Check existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Documentation**: Read the docs in the `/docs` directory

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

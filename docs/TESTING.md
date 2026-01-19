# Testing Documentation

## Overview

This document describes the comprehensive test coverage and CI/CD integration for the LUCA NRW Scraper project.

## Test Structure

### Test Organization

```
tests/
├── conftest.py                      # Pytest configuration and fixtures
├── test_extraction_enhanced.py      # Extraction logic tests
├── test_phone_extraction.py         # Phone number extraction tests
├── test_database_operations.py      # Database layer tests
├── test_django_views.py             # Django views tests
└── [existing test files...]

telis_recruitment/
├── leads/tests.py                   # Lead model and functionality tests
├── scraper_control/tests.py         # Scraper control tests
├── email_templates/tests.py         # Email template tests
├── pages/tests.py                   # Landing pages tests
├── reports/tests.py                 # Reports tests
└── [other apps]/tests.py
```

### Test Categories

Tests are organized using pytest markers:

- `@pytest.mark.unit` - Fast unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.django` - Django-specific tests

## Running Tests

### Local Testing

#### Run All Tests
```bash
# Scraper tests
pytest tests/

# Django tests
cd telis_recruitment
python manage.py test
```

#### Run Specific Test Categories
```bash
# Only unit tests (fast)
pytest tests/ -m "unit"

# Skip slow tests
pytest tests/ -m "not slow"

# Only integration tests
pytest tests/ -m "integration"

# Django tests only
pytest tests/ -m "django"
```

#### Run with Coverage
```bash
# Scraper tests with coverage
pytest tests/ --cov=luca_scraper --cov=stream2_extraction_layer --cov-report=html

# Django tests with coverage
cd telis_recruitment
pytest --cov=. --cov-report=html --cov-report=term-missing
```

#### Run Specific Test Files
```bash
# Test extraction logic
pytest tests/test_extraction_enhanced.py -v

# Test phone extraction
pytest tests/test_phone_extraction.py -v

# Test database operations
pytest tests/test_database_operations.py -v

# Test Django views
pytest tests/test_django_views.py -v
```

### Code Quality Checks

#### Linting
```bash
# Flake8
flake8 luca_scraper stream2_extraction_layer stream3_scoring_layer

# Django-specific
flake8 telis_recruitment
```

#### Formatting
```bash
# Check formatting with Black
black --check luca_scraper stream2_extraction_layer stream3_scoring_layer telis_recruitment

# Auto-format code
black luca_scraper stream2_extraction_layer stream3_scoring_layer telis_recruitment
```

#### Import Sorting
```bash
# Check import sorting
isort --check-only luca_scraper stream2_extraction_layer stream3_scoring_layer telis_recruitment

# Fix import sorting
isort luca_scraper stream2_extraction_layer stream3_scoring_layer telis_recruitment
```

#### Type Checking
```bash
# Run mypy type checker
mypy luca_scraper stream2_extraction_layer stream3_scoring_layer --ignore-missing-imports
```

#### Pylint
```bash
# Run pylint on scraper code
pylint luca_scraper stream2_extraction_layer stream3_scoring_layer

# Run pylint on Django code
pylint telis_recruitment --load-plugins=pylint_django --django-settings-module=telis.settings
```

## CI/CD Integration

### GitHub Actions Workflows

The project has three main CI workflows:

#### 1. Scraper Tests CI (`.github/workflows/scraper-ci.yml`)

**Triggers:**
- Push to main branch (scraper code changes)
- Pull requests to main

**Jobs:**
- **test**: Run pytest with coverage for scraper code
- **lint**: Flake8, Black, isort, pylint checks
- **type-check**: MyPy type checking
- **integration-tests**: Integration and slow tests

**Configuration:**
```yaml
# Only run on scraper-related changes
paths:
  - 'luca_scraper/**'
  - 'stream2_extraction_layer/**'
  - 'stream3_scoring_layer/**'
  - 'tests/**'
  - '*.py'
  - 'requirements.txt'
```

#### 2. Django CI (`.github/workflows/django-ci.yml`)

**Triggers:**
- Push to main branch (Django code changes)
- Pull requests to main

**Jobs:**
- **test**: Django tests with migrations check
- **lint**: Code quality checks
- **security**: Bandit and safety checks

**Configuration:**
```yaml
# Only run on Django-related changes
paths:
  - 'telis_recruitment/**'
  - '.github/workflows/django-ci.yml'
```

#### 3. Nightly Scraper (`.github/workflows/nightly-scraper.yml`)

**Triggers:**
- Scheduled at 02:00 UTC daily
- Manual trigger via GitHub Actions UI

**Purpose:**
- Automated scraper runs
- CSV generation and import
- Artifact storage (30 days)

### Coverage Reports

Coverage reports are automatically generated and uploaded:

- **Scraper Coverage**: Codecov integration for scraper tests
- **Django Coverage**: Codecov integration for Django tests
- **HTML Reports**: Available as GitHub Actions artifacts

Access coverage reports:
1. Go to Actions tab in GitHub
2. Select a workflow run
3. Download coverage artifacts
4. Open `htmlcov/index.html` in browser

## Test Coverage Goals

### Current Coverage

- **Extraction Layer**: Comprehensive email, name, and role extraction tests
- **Phone Extraction**: Pattern matching, validation, and blacklist tests
- **Database Layer**: Connection management, schema, and operations tests
- **Django Views**: CRM dashboard, lead management, and API tests
- **Django Models**: Lead lifecycle, scraper control, and data integrity tests

### Coverage Targets

| Component | Target Coverage | Current Status |
|-----------|----------------|----------------|
| Extraction Logic | 80%+ | ✅ Comprehensive |
| Database Layer | 75%+ | ✅ Good |
| Django Models | 85%+ | ✅ Existing |
| Django Views | 70%+ | ✅ New tests added |
| API Endpoints | 75%+ | ✅ Covered |
| Utility Functions | 60%+ | ⚠️ Partial |

## Best Practices

### Writing Tests

1. **Use descriptive test names**
   ```python
   def test_extract_email_with_obfuscation():
       """Test extraction of obfuscated email addresses"""
   ```

2. **Arrange-Act-Assert pattern**
   ```python
   def test_example():
       # Arrange
       text = "test input"
       # Act
       result = extract_function(text)
       # Assert
       assert result == expected
   ```

3. **Use fixtures for common setup**
   ```python
   @pytest.fixture
   def sample_lead():
       return Lead.objects.create(name="Test", email="test@example.com")
   ```

4. **Mark slow tests**
   ```python
   @pytest.mark.slow
   def test_large_dataset():
       # Test that takes > 1 second
   ```

### Database Tests

- Use `TransactionTestCase` for Django tests requiring database
- Clean up test data in `tearDown()`
- Use factories (factory-boy) for complex model creation

### Mocking External Services

```python
from unittest.mock import patch, MagicMock

@patch('module.external_service')
def test_with_mock(mock_service):
    mock_service.return_value = expected_result
    # Test code
```

## Continuous Improvement

### Adding New Tests

1. Identify untested code paths using coverage reports
2. Write tests following existing patterns
3. Run locally before committing
4. Verify CI passes

### Maintaining Tests

- Keep tests up-to-date with code changes
- Remove obsolete tests
- Refactor duplicate test code into fixtures
- Update documentation when test structure changes

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

**Django Settings**
```bash
# Set Django settings module
export DJANGO_SETTINGS_MODULE=telis.settings
pytest tests/ -m django
```

**Database Lock**
```bash
# Use parallel testing carefully
python manage.py test --parallel=2
```

**Slow Tests**
```bash
# Skip slow tests during development
pytest tests/ -m "not slow"
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Coverage.py](https://coverage.readthedocs.io/)
- [GitHub Actions](https://docs.github.com/en/actions)

## Contact

For questions or issues with testing:
- Open an issue on GitHub
- Check existing test files for examples
- Review CI logs for failures

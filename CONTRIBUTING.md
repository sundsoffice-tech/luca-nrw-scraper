# Contributing to Luca NRW Scraper

Thank you for your interest in contributing to the Luca NRW Scraper project! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Project Structure](#project-structure)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style Guidelines](#code-style-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Project Structure

The project consists of several main components:

```
luca-nrw-scraper/
├── telis_recruitment/          # Django CRM application
│   ├── leads/                  # Leads management app
│   │   ├── models.py          # Data models
│   │   ├── views.py           # API views
│   │   ├── serializers.py     # REST serializers
│   │   ├── utils/             # Utility modules
│   │   │   └── csv_import.py  # CSV import utilities
│   │   └── management/        # Django management commands
│   ├── telis/                 # Project settings
│   │   ├── settings.py        # Django settings
│   │   └── config.py          # Configuration constants
│   └── requirements.txt       # Python dependencies
├── dashboard/                  # Flask dashboard
├── scraper modules            # Web scraping functionality
├── cleanup.py                 # Database cleanup script
├── cleanup_bad_leads.py       # Advanced cleanup with validation
└── README.md                  # Project documentation
```

## Development Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- Virtual environment tool (venv or virtualenv)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/sundsoffice-tech/luca-nrw-scraper.git
   cd luca-nrw-scraper
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # Install root project dependencies
   pip install -r requirements.txt
   
   # Install Django CRM dependencies
   cd telis_recruitment
   pip install -r requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   # In telis_recruitment directory
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize the database**
   ```bash
   cd telis_recruitment
   python manage.py migrate
   python manage.py createsuperuser
   ```

## Running Tests

### Django Application Tests

The Django CRM application has comprehensive test coverage:

```bash
cd telis_recruitment
python manage.py test leads
```

Run specific test classes:
```bash
python manage.py test leads.tests.LeadModelTest
python manage.py test leads.tests.OptInAPITest
```

Run with verbose output:
```bash
python manage.py test leads --verbosity=2
```

### Code Quality Checks

**Syntax validation:**
```bash
python3 -m py_compile path/to/file.py
```

**Check all Python files:**
```bash
find . -name "*.py" -exec python3 -m py_compile {} \;
```

## Code Style Guidelines

### Python Code Style

We follow PEP 8 style guidelines with some project-specific conventions:

#### General Principles

- **Readability counts**: Write clear, self-documenting code
- **Consistency**: Follow existing code patterns
- **DRY (Don't Repeat Yourself)**: Extract common logic into utilities

#### Specific Guidelines

**1. Imports**
- Standard library imports first
- Third-party imports second
- Local imports last
- Group imports with blank lines

```python
import json
import logging
from pathlib import Path

from django.http import JsonResponse
from django.conf import settings

from .models import Lead
from .utils import process_csv
```

**2. Naming Conventions**
- **Functions/Variables**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private methods**: `_leading_underscore`

```python
# Good
def process_lead_data(lead_data):
    MAX_RETRIES = 3
    lead = Lead()
    return _validate_lead(lead)

class CSVImporter:
    pass
```

**3. Documentation**
- All public functions/classes must have docstrings
- Use Django/Google docstring format
- Include type hints where appropriate

```python
def import_csv(file_path: str, dry_run: bool = False) -> dict:
    """
    Import leads from CSV file.
    
    Args:
        file_path: Path to the CSV file
        dry_run: If True, only validate without saving
        
    Returns:
        Dictionary with import statistics
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist
    """
    pass
```

**4. Error Handling**
- Always catch specific exceptions, not bare `except:`
- Log errors with appropriate level (error, warning, info)
- Provide meaningful error messages to users

```python
try:
    lead = Lead.objects.get(email=email)
except Lead.DoesNotExist:
    logger.warning(f"Lead not found: {email}")
    return None
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    raise
```

**5. Security**
- **Always use parametrized queries** for database operations
- Never concatenate user input into SQL queries
- Validate and sanitize all user input
- Use rate limiting for public APIs

```python
# Good - parametrized query
cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))

# Bad - SQL injection risk
cursor.execute(f"DELETE FROM leads WHERE id = {lead_id}")
```

**6. Configuration**
- Don't hardcode values - use configuration
- Read from environment variables via settings
- Use `telis/config.py` for defaults

```python
# Good
from telis.config import API_RATE_LIMIT_OPT_IN

# Bad
rate_limit = '10/m'  # Hardcoded
```

### Django-Specific Guidelines

**1. Views**
- Use class-based views (ViewSets) for CRUD operations
- Use function-based views for custom endpoints
- Always add proper decorators (@csrf_exempt, @ratelimit, etc.)

**2. Models**
- Add `__str__` method to all models
- Use `choices` for enum-like fields
- Add helpful property methods

**3. Serializers**
- Use read-only fields appropriately
- Add custom validation methods when needed

## Pull Request Process

### Before Submitting

1. **Test your changes**
   - Run all existing tests
   - Add new tests for new functionality
   - Ensure all tests pass

2. **Verify code quality**
   - Check Python syntax
   - Follow style guidelines
   - Remove debug code and print statements

3. **Update documentation**
   - Update README if needed
   - Add docstrings to new functions/classes
   - Update CONTRIBUTING.md if changing processes

4. **Check security**
   - No SQL injection vulnerabilities
   - No secrets in code
   - Proper input validation

### Submitting a Pull Request

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Commit your changes**
   - Use clear, descriptive commit messages
   - Keep commits focused and atomic
   ```bash
   git commit -m "Add rate limiting to opt-in API endpoint"
   ```

3. **Push to your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request**
   - Go to GitHub and create a new Pull Request
   - Fill out the PR template with:
     - **Description**: What changes were made and why
     - **Testing**: How you tested the changes
     - **Checklist**: Confirm all requirements are met

5. **PR Review Process**
   - Address reviewer feedback
   - Make requested changes
   - Keep PR focused - don't add unrelated changes

### PR Checklist

Before submitting, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Documentation updated
- [ ] No syntax errors (verified with `python3 -m py_compile`)
- [ ] No security vulnerabilities
- [ ] Commit messages are clear
- [ ] PR description explains changes

## Reporting Issues

### Bug Reports

When reporting bugs, include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: Exact steps to trigger the bug
3. **Expected behavior**: What should happen
4. **Actual behavior**: What actually happens
5. **Environment**: Python version, OS, etc.
6. **Error messages**: Full error messages and stack traces

### Feature Requests

When requesting features, include:

1. **Use case**: Why is this feature needed?
2. **Proposed solution**: How should it work?
3. **Alternatives**: Other approaches you've considered

### Questions

For questions about using the project:

1. Check existing documentation first
2. Search for similar issues
3. Ask clear, specific questions

## Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

## Getting Help

If you need help:

1. Check this CONTRIBUTING.md
2. Review existing issues and PRs
3. Ask questions in your PR
4. Contact the maintainers

Thank you for contributing to Luca NRW Scraper!

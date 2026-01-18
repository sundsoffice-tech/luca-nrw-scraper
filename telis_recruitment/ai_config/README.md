# AI Configuration App

The `ai_config` Django app centralizes AI configuration and usage logging for the LUCA NRW Scraper project.

## Features

- **AI Provider Management**: Manage multiple AI service providers (OpenAI, Perplexity, etc.)
- **Model Configuration**: Configure specific models with custom parameters and costs
- **Budget Control**: Track daily and monthly AI usage budgets
- **Prompt Templates**: Reusable prompt templates with placeholder support
- **Usage Logging**: Comprehensive logging of AI API calls with cost tracking
- **Admin Interface**: Full Django admin integration for easy management

## Models

### AIProvider
Represents an AI service provider (e.g., OpenAI, Perplexity).

### AIModel
Specific models from providers (e.g., gpt-4o-mini, sonar-small) with their configurations.

### AIConfig
Singleton-style configuration for AI parameters, budgets, and defaults.

### PromptTemplate
Reusable prompt templates with variable placeholders.

### AIUsageLog
Logs every AI API call with tokens, cost, latency, and success status.

## Loader Functions

The `ai_config.loader` module provides functions for scraper integration:

### `get_ai_config()`
Returns the active AI configuration or sensible defaults.

```python
from ai_config.loader import get_ai_config

config = get_ai_config()
temperature = config['temperature']
provider = config['default_provider']
model = config['default_model']
```

### `get_prompt(slug)`
Fetches an active prompt template by slug.

```python
from ai_config.loader import get_prompt

template = get_prompt('lead_extraction')
if template:
    prompt = template.format(content="...")
```

### `log_usage(...)`
Logs AI API usage for tracking and cost management.

```python
from ai_config.loader import log_usage

log_usage(
    provider='OpenAI',
    model='gpt-4o-mini',
    prompt_slug='lead_extraction',
    tokens_prompt=100,
    tokens_completion=50,
    cost=0.000075,
    latency_ms=1200,
    success=True,
    request_id='req-123'
)
```

### `check_budget()`
Checks if usage is within daily and monthly budget limits.

```python
from ai_config.loader import check_budget

allowed, info = check_budget()
if not allowed:
    print(f"Budget exceeded! Daily remaining: {info['daily_remaining']} EUR")
else:
    # Proceed with AI request
    pass
```

### `calculate_cost(provider, model, tokens_prompt, tokens_completion)`
Calculates the cost for a given number of tokens.

```python
from ai_config.loader import calculate_cost

cost = calculate_cost('OpenAI', 'gpt-4o-mini', 100, 50)
```

## Integration with Existing Code

The loader functions are designed to be imported by existing scraper modules:

- `learning_engine.py`
- `ai_learning_engine.py`
- `perplexity_learning.py`
- `luca_scraper/config.py`

Instead of hardcoded AI parameters, these modules can now use:

```python
from ai_config.loader import (
    get_ai_config,
    get_prompt,
    log_usage,
    check_budget
)

# Get dynamic configuration
config = get_ai_config()

# Check budget before making requests
allowed, budget_info = check_budget()
if allowed:
    # Make AI request...
    
    # Log usage after request
    log_usage(
        provider=config['default_provider'],
        model=config['default_model'],
        tokens_prompt=prompt_tokens,
        tokens_completion=completion_tokens,
        cost=total_cost,
        latency_ms=request_time,
        success=True
    )
```

## Default Data

The app includes a data migration that creates:

### Providers
- **OpenAI**: with models `gpt-4o-mini` and `gpt-4o`
- **Perplexity**: with model `sonar-small`

### Default Configuration
- Temperature: 0.3
- Top P: 1.0
- Max Tokens: 4000
- Learning Rate: 0.01
- Daily Budget: 5.0 EUR
- Monthly Budget: 150.0 EUR
- Confidence Threshold: 0.35
- Retry Limit: 2
- Timeout: 30 seconds

### Prompt Templates
- **lead_extraction**: Extract lead information from content
- **lead_scoring**: Score lead quality and relevance
- **dork_generation**: Generate optimized search dorks
- **content_analysis**: Analyze content for recruitment relevance
- **data_enrichment**: Enrich lead data with contextual information

## Admin Interface

Access the admin interface at `/admin/` to:

1. **Manage Providers**: Add/edit AI providers and their models inline
2. **Configure AI Settings**: Update active configuration with singleton enforcement
3. **Edit Prompt Templates**: Create and modify reusable prompts
4. **View Usage Logs**: Monitor AI usage with filters and budget statistics

The admin includes:
- Color-coded status badges
- Budget tracking summaries
- Read-only usage logs
- Search and filter capabilities

## Testing

Run tests with:

```bash
cd telis_recruitment
python manage.py test ai_config
```

All 15 tests should pass, covering:
- Model creation and validation
- Singleton behavior for AIConfig
- Cost calculation and overrides
- Loader function behavior
- Budget checking

## Migration

To apply migrations:

```bash
cd telis_recruitment
python manage.py migrate ai_config
```

This will:
1. Create all necessary database tables
2. Load default providers, models, config, and templates

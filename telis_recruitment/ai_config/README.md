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

The loader functions are designed to be imported by existing scraper modules. The following modules have been integrated with `ai_config`:

### Integrated Scraper Modules

#### 1. `learning_engine.py` (Root Level)
Self-learning engine that tracks and optimizes lead generation patterns.

**Integration Features:**
- Optional import with graceful fallback
- Loads AI config on initialization
- Uses config for temperature, max_tokens, and model selection
- Logs info when Django config is available vs. fallback

**Usage Pattern:**
```python
from learning_engine import LearningEngine

engine = LearningEngine(db_path="scraper.db")
# Automatically uses ai_config when available
# Falls back to defaults when Django not configured
```

#### 2. `ai_learning_engine.py` (Root Level)
Active learning system for portal performance tracking and dork optimization.

**Integration Features:**
- Optional import with graceful fallback
- Loads AI config on initialization
- Ready for AI-driven improvements
- Logs config source (Django DB vs. fallback)

**Usage Pattern:**
```python
from ai_learning_engine import ActiveLearningEngine

engine = ActiveLearningEngine(db_path="scraper.db")
# Automatically uses ai_config when available
```

#### 3. `perplexity_learning.py` (Root Level)
Learning engine for Perplexity search optimization.

**Integration Features:**
- Optional import with graceful fallback
- Loads general AI config and Perplexity-specific config from Django
- Retrieves Perplexity provider API URL and model settings
- Falls back to environment variables and defaults

**Usage Pattern:**
```python
from perplexity_learning import PerplexityLearning

pplx = PerplexityLearning(db_path="scraper.db")
# Uses Perplexity config from Django AIProvider/AIModel when available
# Falls back to PERPLEXITY_API_KEY env variable
```

#### 4. `adaptive_system.py` (Root Level)
Adaptive search system coordinating metrics and dork selection.

**Integration Features:**
- Optional import with graceful fallback
- Loads AI config on initialization
- Ready for AI-driven adaptive strategies
- Logs config source for debugging

**Usage Pattern:**
```python
from adaptive_system import AdaptiveSearchSystem

system = AdaptiveSearchSystem(
    all_dorks=dork_list,
    metrics_db_path="metrics.db"
)
# Automatically uses ai_config when available
```

#### 5. `luca_scraper/config.py` (Central Configuration)
Central configuration module with priority-based config loading.

**Integration Features:**
- `get_config()` function with 3-tier priority:
  1. Django DB via ai_config (highest priority)
  2. Environment variables (medium priority)
  3. Hardcoded defaults (fallback)
- Optional import with graceful fallback
- Documented priority order in docstrings

**Usage Pattern:**
```python
from luca_scraper.config import get_config

# Get full config
config = get_config()
temperature = config['temperature']
model = config['default_model']

# Get specific parameter
temp = get_config('temperature')
model = get_config('default_model')
```

### Generic Integration Pattern

All integrated modules follow this pattern:

```python
# Optional Django ai_config integration
# Falls back gracefully when Django is not available or configured
try:
    from telis_recruitment.ai_config.loader import (
        get_ai_config,
        get_prompt,
        log_usage,
        check_budget
    )
    AI_CONFIG_AVAILABLE = True
except (ImportError, Exception):
    AI_CONFIG_AVAILABLE = False
    # Fallback defaults when ai_config is not available
    def get_ai_config():
        return {
            'temperature': 0.3,
            'max_tokens': 4000,
            'default_provider': 'OpenAI',
            'default_model': 'gpt-4o-mini',
            # ... other defaults
        }
    
    def get_prompt(slug: str):
        return None
    
    def log_usage(*args, **kwargs):
        pass
    
    def check_budget():
        return True, {...}

# In class __init__:
self.ai_config = get_ai_config()
if AI_CONFIG_AVAILABLE:
    logger.info(f"AI config loaded from Django DB")
else:
    logger.info("AI config using fallback defaults")
```

### Backwards Compatibility

**All scraper modules remain backwards compatible:**
- Running without Django installed/configured works seamlessly
- `scriptname.py --once` continues to work standalone
- No database required for basic operation
- Graceful degradation to environment variables and hardcoded defaults

### Configuration Priority (luca_scraper/config.py)

The `get_config()` function implements a 3-tier priority system:

1. **Django DB** (Highest Priority): Values from `AIConfig` model via `ai_config.loader`
2. **Environment Variables** (Medium Priority): `AI_TEMPERATURE`, `AI_MAX_TOKENS`, `AI_MODEL`, `AI_PROVIDER`
3. **Hardcoded Defaults** (Fallback): Sensible defaults for standalone operation

Example:
```python
# Priority 1: Django DB (if available)
# Priority 2: Environment variable AI_TEMPERATURE=0.5
# Priority 3: Default 0.3

temperature = get_config('temperature')  # Returns highest priority value
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

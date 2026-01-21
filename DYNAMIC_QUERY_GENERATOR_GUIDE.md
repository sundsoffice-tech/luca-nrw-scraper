# DynamicQueryGenerator - AI-Powered Query Expansion

## Overview

The DynamicQueryGenerator is a new AI-powered module that implements **Query Fan-Out** strategy to expand search queries and generate broader lead discoveries.

## Key Features

### 1. Environment-Based Activation
- **Automatically activates** when `OPENAI_API_KEY` environment variable is set
- **Gracefully falls back** to basic queries when API key is not available
- No code changes required to enable/disable AI features

### 2. Query Fan-Out Strategy

The module implements two complementary expansion techniques:

#### Generalization
Creates broader versions of the original query by:
- Removing specific constraints (location, company name, etc.)
- Using synonyms and related terms
- Supporting both German and English variations

**Example:**
```
Input:  "Sales Manager Hamburg"
Output: "Sales Hamburg"
        "Vertrieb Hamburg"
        "Sales Mitarbeiter Hamburg"
```

#### Follow-ups
Generates related queries to discover additional leads:
- Adjacent job titles and roles
- Alternative positions with similar responsibilities
- Cross-platform and cross-industry variations

**Example:**
```
Input:  "Sales Manager"
Output: "Business Development Manager"
        "Account Manager"
        "Vertriebsleiter"
        "Key Account Manager"
```

## Usage Examples

### Basic Query Expansion

```python
import asyncio
from luca_scraper.ai import DynamicQueryGenerator

async def main():
    generator = DynamicQueryGenerator()
    
    # Check if AI features are enabled
    if generator.is_enabled():
        print("AI query expansion is ACTIVE")
    else:
        print("AI query expansion is DISABLED (no OPENAI_API_KEY)")
    
    # Generate expanded queries
    queries = await generator.generate_expanded_queries(
        base_query="Sales Manager Hamburg",
        industry="B2B Software",
        count=5,
        include_original=True
    )
    
    # Process results
    for query in queries:
        print(f"{query['type']:12} | {query['query']}")
        print(f"             | Confidence: {query['confidence']}%")
        print(f"             | Reason: {query['reason']}")
        print()

asyncio.run(main())
```

**Output (with OPENAI_API_KEY set):**
```
original     | Sales Manager Hamburg
             | Confidence: 100%
             | Reason: Original base query

generalized  | Sales Hamburg
             | Confidence: 90%
             | Reason: Generalized location-based search

generalized  | Vertrieb Hamburg
             | Confidence: 85%
             | Reason: German synonym for sales

follow-up    | Business Development Hamburg
             | Confidence: 80%
             | Reason: Related role for lead generation

follow-up    | Account Manager Hamburg
             | Confidence: 75%
             | Reason: Adjacent sales position
```

### Google Dork Generation with Fan-Out

```python
import asyncio
from luca_scraper.ai import DynamicQueryGenerator

async def main():
    generator = DynamicQueryGenerator()
    
    # Generate Google dorks for B2B industry
    dorks = await generator.generate_dorks_with_fanout(
        industry="Software Development",
        count=5
    )
    
    print("Generated Google Dorks:")
    for i, dork in enumerate(dorks, 1):
        print(f"{i}. {dork}")

asyncio.run(main())
```

**Output:**
```
Generated Google Dorks:
1. intitle:"Team" "Sales" Software Development
2. filetype:pdf "Lebenslauf" "Software Development"
3. site:linkedin.com/in/ "Software Development" "open to work"
4. "stellengesuch" "Software Development" "verfügbar ab"
5. site:xing.com/profile "Software Development" "offen für angebote"
```

### Integration with Existing Code

The DynamicQueryGenerator integrates seamlessly with existing query generation:

```python
from luca_scraper.ai import generate_smart_dorks, DynamicQueryGenerator

async def generate_queries_for_industry(industry: str):
    # Option 1: Use existing function (enhanced with Query Fan-Out)
    basic_dorks = await generate_smart_dorks(industry, count=5)
    
    # Option 2: Use new DynamicQueryGenerator for more control
    generator = DynamicQueryGenerator()
    advanced_dorks = await generator.generate_dorks_with_fanout(industry, count=5)
    
    return basic_dorks + advanced_dorks
```

## Environment Configuration

### Required Environment Variables

```bash
# Required for AI-powered query expansion
export OPENAI_API_KEY="sk-..."

# Optional: Override default model
export OPENAI_MODEL="gpt-4o-mini"  # default

# Optional: HTTP timeout for API calls
export HTTP_TIMEOUT=30  # seconds, default from config
```

### Configuration in .env File

```env
# AI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o-mini

# Optional: Adjust HTTP timeout
HTTP_TIMEOUT=30
```

## Architecture

### Class Hierarchy
```
DynamicQueryGenerator
├── __init__()                      # Initialize with API key detection
├── is_enabled()                    # Check if AI features are active
├── generate_expanded_queries()     # Main query expansion method
├── generate_dorks_with_fanout()    # Specialized dork generation
├── _build_system_prompt()          # Build AI system instructions
├── _build_user_prompt()            # Build user request
├── _call_openai_api()              # Make API calls
├── _parse_response()               # Parse AI responses
└── _fallback_queries()             # Graceful fallback
```

### Integration Points

1. **Module Export** (`luca_scraper/ai/__init__.py`)
   - DynamicQueryGenerator is exported alongside other AI functions
   - Can be imported as: `from luca_scraper.ai import DynamicQueryGenerator`

2. **Enhanced Existing Function** (`luca_scraper/ai/perplexity.py`)
   - `generate_smart_dorks()` now includes Query Fan-Out in prompts
   - Backward compatible - existing code continues to work

3. **Configuration** (`luca_scraper/config/env_loader.py`)
   - Uses existing OPENAI_API_KEY configuration
   - No new environment variables required

## Query Fan-Out Strategy Details

### Why Query Fan-Out?

Traditional single-query searches miss many potential leads:
- **Location constraints** eliminate broader regional opportunities
- **Specific job titles** miss adjacent roles with similar responsibilities
- **Single platforms** overlook candidates on alternative sites

Query Fan-Out solves this by automatically generating multiple related queries.

### Generalization Examples

| Original Query | Generalized Queries |
|---------------|---------------------|
| "Sales Manager Hamburg" | "Sales Hamburg", "Vertrieb Hamburg", "Sales NRW" |
| "Java Developer Berlin" | "Java Berlin", "Software Developer Berlin", "Backend Berlin" |
| "Marketing Manager Munich" | "Marketing Munich", "Marketing Bayern", "Digital Marketing Munich" |

### Follow-up Examples

| Original Query | Follow-up Queries |
|---------------|-------------------|
| "Sales Manager" | "Business Development", "Account Manager", "Key Account Manager" |
| "Java Developer" | "Backend Developer", "Software Engineer", "Full Stack Developer" |
| "Marketing Manager" | "Digital Marketing", "Content Manager", "Growth Manager" |

## Testing

### Unit Tests

Run the comprehensive unit test suite:

```bash
cd /home/runner/work/luca-nrw-scraper/luca-nrw-scraper
pytest tests/test_dynamic_query_generator.py -v
```

### Validation Script

Run the validation script to verify all functionality:

```bash
python validate_query_generator.py
```

This script validates:
- ✅ Fallback behavior without API key
- ✅ AI activation with API key
- ✅ Module import and integration
- ✅ Query Fan-Out in existing modules
- ✅ Documentation completeness

## Performance Considerations

### API Calls
- Each query expansion makes **one API call** to OpenAI
- Response time: typically 1-3 seconds
- Cost: ~$0.0001 per request (with gpt-4o-mini)

### Caching
- Responses are not cached by default
- Consider implementing caching for repeated queries in production

### Rate Limiting
- OpenAI API has rate limits (tier-dependent)
- Implement exponential backoff for production use
- Current implementation includes basic error handling

## Troubleshooting

### "AI features DISABLED" message
**Problem:** Generator always shows as disabled
**Solution:** Set OPENAI_API_KEY environment variable

```bash
export OPENAI_API_KEY="sk-..."
```

### Empty query list returned
**Problem:** `generate_expanded_queries()` returns empty list
**Causes:**
1. API key not set → Check environment variable
2. API call failed → Check network connectivity
3. Rate limit exceeded → Wait and retry
4. Invalid API key → Verify key is correct

**Solution:** Check logs for error messages

### JSON parsing errors
**Problem:** "Unexpected response format" in logs
**Cause:** OpenAI API returned non-JSON response
**Solution:** This is handled automatically with fallback to base query

## Future Enhancements

Potential improvements for future versions:

1. **Response Caching**
   - Cache expanded queries to reduce API calls
   - TTL-based cache invalidation

2. **Configurable Temperature**
   - Allow tuning creativity vs consistency
   - Environment variable: `OPENAI_TEMPERATURE`

3. **Batch Processing**
   - Expand multiple queries in single API call
   - Reduce latency for bulk operations

4. **Analytics**
   - Track which query types perform best
   - Optimize Fan-Out ratios based on results

5. **Custom Prompts**
   - Allow custom system/user prompts
   - Industry-specific prompt templates

## Support

For issues or questions:
1. Check validation script output: `python validate_query_generator.py`
2. Review logs for error messages
3. Verify environment variables are set correctly
4. Check OpenAI API status: https://status.openai.com/

## License

Part of the LUCA NRW Scraper project.

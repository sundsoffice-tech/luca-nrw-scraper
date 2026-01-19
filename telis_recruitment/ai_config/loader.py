"""
AI Configuration Loader

This module provides functions to load AI configuration, prompts, and log usage.
Designed to be imported by scraper modules to avoid hardcoded AI parameters.

All Django imports are lazy to support standalone operation without Django.
"""

from typing import Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import timedelta


def get_ai_config() -> Dict[str, Any]:
    """
    Get the active AI configuration or return sensible defaults.
    
    Returns:
        dict: Configuration dictionary with all AI parameters
        
    Example:
        config = get_ai_config()
        temperature = config['temperature']
        provider = config['default_provider']
    """
    try:
        # Lazy import of Django models - will fail if Django not configured
        from .models import AIConfig
        
        config = AIConfig.objects.filter(is_active=True).first()
        
        if config:
            return {
                'temperature': config.temperature,
                'top_p': config.top_p,
                'max_tokens': config.max_tokens,
                'learning_rate': config.learning_rate,
                'daily_budget': float(config.daily_budget),
                'monthly_budget': float(config.monthly_budget),
                'confidence_threshold': config.confidence_threshold,
                'retry_limit': config.retry_limit,
                'timeout_seconds': config.timeout_seconds,
                'default_provider': config.default_provider.name if config.default_provider else None,
                'default_model': config.default_model.name if config.default_model else None,
                'default_model_display': config.default_model.display_name if config.default_model else None,
            }
    except Exception:
        # Catch ALL exceptions including:
        # - django.core.exceptions.ImproperlyConfigured (Django not configured)
        # - ImportError (Django not installed)
        # - Database errors (table doesn't exist)
        # Fall through to return defaults
        pass
    
    # Return sensible defaults if no config found OR Django not configured
    return {
        'temperature': 0.3,
        'top_p': 1.0,
        'max_tokens': 4000,
        'learning_rate': 0.01,
        'daily_budget': 5.0,
        'monthly_budget': 150.0,
        'confidence_threshold': 0.35,
        'retry_limit': 2,
        'timeout_seconds': 30,
        'default_provider': 'OpenAI',
        'default_model': 'gpt-4o-mini',
        'default_model_display': 'GPT-4o Mini',
    }


def get_prompt(slug: str) -> Optional[str]:
    """
    Fetch an active prompt template by slug.
    
    Args:
        slug: Unique slug identifier for the prompt template
        
    Returns:
        str: Prompt template content, or None if not found
        
    Example:
        template = get_prompt('lead_extraction')
        if template:
            prompt = template.format(name="John Doe", company="Acme Inc")
    """
    from .models import PromptTemplate
    
    try:
        template = PromptTemplate.objects.filter(slug=slug, is_active=True).first()
        if template:
            return template.content
    except Exception:
        pass
    
    return None


def log_usage(
    provider: str,
    model: str,
    prompt_slug: str = "",
    tokens_prompt: int = 0,
    tokens_completion: int = 0,
    cost: float = 0.0,
    latency_ms: int = 0,
    success: bool = True,
    request_id: Optional[str] = None,
    error_message: str = "",
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log AI API usage for tracking and cost management.
    
    Args:
        provider: Provider name (e.g., 'OpenAI', 'Perplexity')
        model: Model name (e.g., 'gpt-4o-mini', 'sonar-small')
        prompt_slug: Optional slug of the prompt template used
        tokens_prompt: Number of prompt tokens used
        tokens_completion: Number of completion tokens used
        cost: Cost in EUR
        latency_ms: Request latency in milliseconds
        success: Whether the request succeeded
        request_id: Optional correlation ID for grouping related requests
        error_message: Error message if success is False
        metadata: Optional additional metadata as dict
        
    Example:
        log_usage(
            provider='OpenAI',
            model='gpt-4o-mini',
            prompt_slug='lead_extraction',
            tokens_prompt=100,
            tokens_completion=50,
            cost=0.00015,
            latency_ms=1200,
            success=True,
            request_id='req-123'
        )
    """
    from .models import AIUsageLog
    
    try:
        AIUsageLog.objects.create(
            provider=provider,
            model=model,
            prompt_slug=prompt_slug,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            cost=Decimal(str(cost)),
            latency_ms=latency_ms,
            success=success,
            error_message=error_message,
            request_id=request_id or "",
            metadata=metadata or {}
        )
    except Exception:
        # Silently fail if logging doesn't work (e.g., during migrations)
        # Don't break the main application flow
        pass


def check_budget() -> Tuple[bool, Dict[str, float]]:
    """
    Check if AI usage is within daily and monthly budget limits.
    
    Returns:
        tuple: (allowed: bool, budget_info: dict)
            - allowed: True if usage is within budget
            - budget_info: Dictionary with budget details
                - daily_spent: Amount spent today
                - daily_budget: Daily budget limit
                - daily_remaining: Remaining daily budget
                - monthly_spent: Amount spent this month
                - monthly_budget: Monthly budget limit
                - monthly_remaining: Remaining monthly budget
                
    Example:
        allowed, info = check_budget()
        if not allowed:
            print(f"Budget exceeded! Daily: {info['daily_remaining']} EUR remaining")
        else:
            # Proceed with AI request
            pass
    """
    try:
        from django.utils import timezone
        from django.db.models import Sum
        from .models import AIConfig, AIUsageLog
        
        config = get_ai_config()
        daily_budget = config['daily_budget']
        monthly_budget = config['monthly_budget']
        
        # Calculate today's spending
        today = timezone.now().date()
        today_spent = AIUsageLog.objects.filter(
            created_at__date=today
        ).aggregate(total=Sum('cost'))['total'] or Decimal('0')
        today_spent = float(today_spent)
        
        # Calculate this month's spending
        first_day_of_month = today.replace(day=1)
        month_spent = AIUsageLog.objects.filter(
            created_at__date__gte=first_day_of_month
        ).aggregate(total=Sum('cost'))['total'] or Decimal('0')
        month_spent = float(month_spent)
        
        # Calculate remaining budgets
        daily_remaining = daily_budget - today_spent
        monthly_remaining = monthly_budget - month_spent
        
        # Check if both budgets allow usage
        allowed = daily_remaining > 0 and monthly_remaining > 0
        
        budget_info = {
            'daily_spent': today_spent,
            'daily_budget': daily_budget,
            'daily_remaining': daily_remaining,
            'monthly_spent': month_spent,
            'monthly_budget': monthly_budget,
            'monthly_remaining': monthly_remaining,
        }
        
        return allowed, budget_info
    except Exception:
        # If Django is not configured, return defaults
        config = get_ai_config()
        daily_budget = config['daily_budget']
        monthly_budget = config['monthly_budget']
        
        return True, {
            'daily_spent': 0.0,
            'daily_budget': daily_budget,
            'daily_remaining': daily_budget,
            'monthly_spent': 0.0,
            'monthly_budget': monthly_budget,
            'monthly_remaining': monthly_budget,
        }


def get_model_costs(provider: str, model: str) -> Tuple[float, float]:
    """
    Get the cost per 1K tokens for a specific model.
    
    Args:
        provider: Provider name
        model: Model name
        
    Returns:
        tuple: (prompt_cost, completion_cost) per 1K tokens in EUR
        
    Example:
        prompt_cost, completion_cost = get_model_costs('OpenAI', 'gpt-4o-mini')
    """
    from .models import AIProvider, AIModel
    
    try:
        provider_obj = AIProvider.objects.filter(name=provider).first()
        if provider_obj:
            model_obj = AIModel.objects.filter(
                provider=provider_obj, 
                name=model
            ).first()
            if model_obj:
                return (
                    float(model_obj.get_prompt_cost()),
                    float(model_obj.get_completion_cost())
                )
        
        # Return defaults if not found
        return (0.0, 0.0)
    except Exception:
        return (0.0, 0.0)


def calculate_cost(
    provider: str,
    model: str,
    tokens_prompt: int,
    tokens_completion: int
) -> float:
    """
    Calculate the cost for a given number of tokens.
    
    Args:
        provider: Provider name
        model: Model name
        tokens_prompt: Number of prompt tokens
        tokens_completion: Number of completion tokens
        
    Returns:
        float: Total cost in EUR
        
    Example:
        cost = calculate_cost('OpenAI', 'gpt-4o-mini', 100, 50)
    """
    prompt_cost, completion_cost = get_model_costs(provider, model)
    
    # Calculate cost (costs are per 1K tokens)
    total_cost = (
        (tokens_prompt / 1000.0) * prompt_cost +
        (tokens_completion / 1000.0) * completion_cost
    )
    
    return total_cost

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class AIProvider(models.Model):
    """
    AI Service Provider (e.g., OpenAI, Perplexity)
    """
    name = models.CharField(max_length=100, unique=True, verbose_name="Provider Name")
    base_url = models.URLField(blank=True, verbose_name="Base API URL")
    cost_per_1k_tokens_prompt = models.DecimalField(
        max_digits=10, 
        decimal_places=6, 
        default=0.0,
        validators=[MinValueValidator(0)],
        verbose_name="Cost per 1K Prompt Tokens (EUR)"
    )
    cost_per_1k_tokens_completion = models.DecimalField(
        max_digits=10, 
        decimal_places=6, 
        default=0.0,
        validators=[MinValueValidator(0)],
        verbose_name="Cost per 1K Completion Tokens (EUR)"
    )
    active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Provider"
        verbose_name_plural = "AI Providers"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} {'(Active)' if self.active else '(Inactive)'}"


class AIModel(models.Model):
    """
    Specific AI Model from a provider (e.g., gpt-4o-mini, sonar-small)
    """
    provider = models.ForeignKey(
        AIProvider, 
        on_delete=models.CASCADE, 
        related_name='models',
        verbose_name="Provider"
    )
    name = models.CharField(max_length=100, verbose_name="Model Name (slug)")
    display_name = models.CharField(max_length=200, verbose_name="Display Name")
    
    # Default parameters
    default_temperature = models.FloatField(
        default=0.3, 
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        verbose_name="Default Temperature"
    )
    default_top_p = models.FloatField(
        default=1.0, 
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Default Top P"
    )
    default_max_tokens = models.IntegerField(
        default=4000, 
        validators=[MinValueValidator(1)],
        verbose_name="Default Max Tokens"
    )
    
    # Cost overrides (if different from provider defaults)
    cost_per_1k_tokens_prompt = models.DecimalField(
        max_digits=10, 
        decimal_places=6, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Cost Override per 1K Prompt Tokens (EUR)",
        help_text="Leave blank to use provider default"
    )
    cost_per_1k_tokens_completion = models.DecimalField(
        max_digits=10, 
        decimal_places=6, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name="Cost Override per 1K Completion Tokens (EUR)",
        help_text="Leave blank to use provider default"
    )
    
    active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Model"
        verbose_name_plural = "AI Models"
        ordering = ['provider', 'name']
        unique_together = [['provider', 'name']]

    def __str__(self):
        return f"{self.provider.name}/{self.name}"
    
    def get_prompt_cost(self):
        """Return the effective cost per 1K prompt tokens"""
        if self.cost_per_1k_tokens_prompt is not None:
            return self.cost_per_1k_tokens_prompt
        return self.provider.cost_per_1k_tokens_prompt
    
    def get_completion_cost(self):
        """Return the effective cost per 1K completion tokens"""
        if self.cost_per_1k_tokens_completion is not None:
            return self.cost_per_1k_tokens_completion
        return self.provider.cost_per_1k_tokens_completion


class AIConfig(models.Model):
    """
    Singleton-style AI Configuration
    Should only have one active instance at a time
    """
    # Model parameters
    temperature = models.FloatField(
        default=0.3, 
        validators=[MinValueValidator(0), MaxValueValidator(2)],
        verbose_name="Temperature"
    )
    top_p = models.FloatField(
        default=1.0, 
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Top P"
    )
    max_tokens = models.IntegerField(
        default=4000, 
        validators=[MinValueValidator(1)],
        verbose_name="Max Tokens"
    )
    learning_rate = models.FloatField(
        default=0.01, 
        validators=[MinValueValidator(0)],
        verbose_name="Learning Rate"
    )
    
    # Budget management
    daily_budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=5.0,
        validators=[MinValueValidator(0)],
        verbose_name="Daily Budget (EUR)"
    )
    monthly_budget = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=150.0,
        validators=[MinValueValidator(0)],
        verbose_name="Monthly Budget (EUR)"
    )
    
    # Quality thresholds
    confidence_threshold = models.FloatField(
        default=0.35, 
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Confidence Threshold"
    )
    
    # Retry and timeout settings
    retry_limit = models.IntegerField(
        default=2, 
        validators=[MinValueValidator(0)],
        verbose_name="Retry Limit"
    )
    timeout_seconds = models.IntegerField(
        default=30, 
        validators=[MinValueValidator(1)],
        verbose_name="Timeout (seconds)"
    )
    
    # Default provider and model
    default_provider = models.ForeignKey(
        AIProvider,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_configs',
        verbose_name="Default Provider"
    )
    default_model = models.ForeignKey(
        AIModel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_configs',
        verbose_name="Default Model"
    )
    
    # Metadata
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Configuration"
        verbose_name_plural = "AI Configurations"
        ordering = ['-is_active', '-created_at']

    def __str__(self):
        return f"AI Config {'(Active)' if self.is_active else '(Inactive)'} - Updated {self.updated_at.strftime('%Y-%m-%d')}"
    
    def save(self, *args, **kwargs):
        """Ensure only one active config exists"""
        if self.is_active:
            # Deactivate all other configs
            AIConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate that default_model belongs to default_provider"""
        if self.default_model and self.default_provider:
            if self.default_model.provider != self.default_provider:
                raise ValidationError({
                    'default_model': 'Selected model must belong to the default provider.'
                })


class PromptTemplate(models.Model):
    """
    Reusable prompt templates with placeholders
    """
    CATEGORY_CHOICES = [
        ('lead_extraction', 'Lead Extraction'),
        ('lead_scoring', 'Lead Scoring'),
        ('dork_generation', 'Dork Generation'),
        ('content_analysis', 'Content Analysis'),
        ('data_enrichment', 'Data Enrichment'),
        ('other', 'Other'),
    ]
    
    slug = models.SlugField(max_length=100, unique=True, verbose_name="Slug")
    title = models.CharField(max_length=200, verbose_name="Title")
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        default='other',
        verbose_name="Category"
    )
    content = models.TextField(
        verbose_name="Template Content",
        help_text="Use {placeholder} syntax for variables"
    )
    description = models.TextField(blank=True, verbose_name="Description")
    is_active = models.BooleanField(default=True, verbose_name="Active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Prompt Template"
        verbose_name_plural = "Prompt Templates"
        ordering = ['category', 'title']

    def __str__(self):
        return f"{self.title} ({self.slug})"


class AIUsageLog(models.Model):
    """
    Log of AI API usage for tracking and cost management
    """
    provider = models.CharField(max_length=100, verbose_name="Provider")
    model = models.CharField(max_length=100, verbose_name="Model")
    prompt_slug = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="Prompt Template Slug"
    )
    
    # Token usage
    tokens_prompt = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0)],
        verbose_name="Prompt Tokens"
    )
    tokens_completion = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0)],
        verbose_name="Completion Tokens"
    )
    
    # Cost and performance
    cost = models.DecimalField(
        max_digits=10, 
        decimal_places=6, 
        default=0.0,
        validators=[MinValueValidator(0)],
        verbose_name="Cost (EUR)"
    )
    latency_ms = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0)],
        verbose_name="Latency (ms)"
    )
    
    # Status
    success = models.BooleanField(default=True, verbose_name="Success")
    error_message = models.TextField(blank=True, verbose_name="Error Message")
    
    # Correlation and metadata
    request_id = models.CharField(
        max_length=100, 
        blank=True, 
        db_index=True,
        verbose_name="Request ID"
    )
    metadata = models.JSONField(
        default=dict, 
        blank=True,
        verbose_name="Additional Metadata"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "AI Usage Log"
        verbose_name_plural = "AI Usage Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['provider', 'model']),
            models.Index(fields=['success']),
        ]

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.provider}/{self.model} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class DorkPerformance(models.Model):
    """
    Tracks performance of search queries (dorks) across all learning engines.
    Consolidates data from learning_engine, ai_learning_engine, and perplexity_learning.
    """
    query = models.TextField(verbose_name="Search Query", db_index=True)
    query_hash = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Query Hash",
        help_text="MD5 hash of the query for fast lookups"
    )
    times_used = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Times Used"
    )
    leads_found = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Leads Found"
    )
    phone_leads = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Leads with Phone"
    )
    success_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Success Rate"
    )
    pool = models.CharField(
        max_length=20,
        default='explore',
        choices=[('core', 'Core'), ('explore', 'Explore')],
        verbose_name="Pool"
    )
    last_used = models.DateTimeField(null=True, blank=True, verbose_name="Last Used")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Dork Performance"
        verbose_name_plural = "Dork Performance Metrics"
        ordering = ['-success_rate', '-phone_leads']
        indexes = [
            models.Index(fields=['-success_rate', '-phone_leads']),
            models.Index(fields=['pool', '-success_rate']),
            models.Index(fields=['-last_used']),
        ]

    def __str__(self):
        return f"{self.query[:50]}... ({self.phone_leads} leads, {self.success_rate:.1%} success)"


class SourcePerformance(models.Model):
    """
    Tracks performance of source domains/portals.
    Consolidates learning from all three engines.
    """
    domain = models.CharField(max_length=255, unique=True, verbose_name="Domain")
    leads_found = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Total Leads Found"
    )
    leads_with_phone = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Leads with Phone"
    )
    avg_quality = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Average Quality Score"
    )
    is_blocked = models.BooleanField(
        default=False,
        verbose_name="Blocked/Disabled"
    )
    blocked_reason = models.TextField(
        blank=True,
        verbose_name="Blocked Reason"
    )
    total_visits = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Total Visits"
    )
    last_visit = models.DateTimeField(null=True, blank=True, verbose_name="Last Visit")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Source Performance"
        verbose_name_plural = "Source Performance Metrics"
        ordering = ['-avg_quality', '-leads_with_phone']
        indexes = [
            models.Index(fields=['-avg_quality', '-leads_with_phone']),
            models.Index(fields=['is_blocked']),
            models.Index(fields=['-last_visit']),
        ]

    def __str__(self):
        status = "🚫 " if self.is_blocked else ""
        return f"{status}{self.domain} ({self.leads_with_phone}/{self.leads_found} leads, {self.avg_quality:.1%} quality)"


class PatternSuccess(models.Model):
    """
    Tracks successful extraction patterns (phone patterns, content signals, etc.).
    Consolidates pattern learning from all engines.
    """
    PATTERN_TYPES = [
        ('phone', 'Phone Pattern'),
        ('domain', 'Domain Pattern'),
        ('query_term', 'Query Term'),
        ('url_path', 'URL Path'),
        ('content_signal', 'Content Signal'),
        ('extraction', 'Extraction Pattern'),
    ]
    
    pattern_type = models.CharField(
        max_length=50,
        choices=PATTERN_TYPES,
        verbose_name="Pattern Type",
        db_index=True
    )
    pattern_value = models.TextField(verbose_name="Pattern Value")
    pattern_hash = models.CharField(
        max_length=64,
        verbose_name="Pattern Hash",
        help_text="Hash of type + value for uniqueness"
    )
    occurrences = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Occurrences"
    )
    confidence = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        verbose_name="Confidence Score"
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Metadata"
    )
    last_success = models.DateTimeField(null=True, blank=True, verbose_name="Last Success")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pattern Success"
        verbose_name_plural = "Pattern Success Metrics"
        ordering = ['-confidence', '-occurrences']
        unique_together = [['pattern_type', 'pattern_hash']]
        indexes = [
            models.Index(fields=['pattern_type', '-confidence']),
            models.Index(fields=['-occurrences']),
            models.Index(fields=['-last_success']),
        ]

    def __str__(self):
        return f"{self.pattern_type}: {self.pattern_value[:50]}... ({self.occurrences}x, {self.confidence:.1%} confidence)"


class TelefonbuchCache(models.Model):
    """
    Cache for phonebook lookup results with TTL.
    Enables automatic cleanup of expired entries.
    """
    query_hash = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Query Hash",
        help_text="Hash of the lookup query"
    )
    query_text = models.TextField(
        verbose_name="Query Text",
        help_text="Original query for debugging"
    )
    results_json = models.JSONField(
        verbose_name="Results (JSON)",
        help_text="Cached lookup results"
    )
    expires_at = models.DateTimeField(
        verbose_name="Expires At",
        db_index=True,
        help_text="Cache expiration timestamp"
    )
    hits = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Cache Hits"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Telefonbuch Cache"
        verbose_name_plural = "Telefonbuch Cache Entries"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['expires_at']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"Cache: {self.query_text[:50]}... (hits: {self.hits}, expires: {self.expires_at.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def is_expired(self):
        """Check if cache entry is expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at

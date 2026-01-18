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

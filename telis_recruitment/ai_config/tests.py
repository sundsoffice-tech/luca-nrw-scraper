from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import AIProvider, AIModel, AIConfig, PromptTemplate, AIUsageLog
from .loader import get_ai_config, get_prompt, log_usage, check_budget, calculate_cost


class AIProviderModelTest(TestCase):
    """Test AIProvider model"""
    
    def test_create_provider(self):
        """Test creating an AI provider"""
        provider = AIProvider.objects.create(
            name='Test Provider',
            base_url='https://api.test.com',
            cost_per_1k_tokens_prompt=Decimal('0.001'),
            cost_per_1k_tokens_completion=Decimal('0.002'),
            active=True
        )
        self.assertEqual(provider.name, 'Test Provider')
        self.assertTrue(provider.active)
        self.assertEqual(provider.cost_per_1k_tokens_prompt, Decimal('0.001'))


class AIModelModelTest(TestCase):
    """Test AIModel model"""
    
    def setUp(self):
        self.provider = AIProvider.objects.create(
            name='Test Provider',
            cost_per_1k_tokens_prompt=Decimal('0.001'),
            cost_per_1k_tokens_completion=Decimal('0.002'),
        )
    
    def test_create_model(self):
        """Test creating an AI model"""
        model = AIModel.objects.create(
            provider=self.provider,
            name='test-model',
            display_name='Test Model',
            default_temperature=0.5,
            default_top_p=0.9,
            default_max_tokens=2000,
        )
        self.assertEqual(model.name, 'test-model')
        self.assertEqual(model.display_name, 'Test Model')
        self.assertEqual(str(model), f"{self.provider.name}/test-model")
    
    def test_model_cost_override(self):
        """Test that model can override provider costs"""
        model = AIModel.objects.create(
            provider=self.provider,
            name='test-model',
            display_name='Test Model',
            cost_per_1k_tokens_prompt=Decimal('0.005'),
            cost_per_1k_tokens_completion=Decimal('0.010'),
        )
        # Should use model-specific costs
        self.assertEqual(model.get_prompt_cost(), Decimal('0.005'))
        self.assertEqual(model.get_completion_cost(), Decimal('0.010'))
    
    def test_model_uses_provider_default_costs(self):
        """Test that model uses provider costs when not overridden"""
        model = AIModel.objects.create(
            provider=self.provider,
            name='test-model',
            display_name='Test Model',
        )
        # Should use provider default costs
        self.assertEqual(model.get_prompt_cost(), self.provider.cost_per_1k_tokens_prompt)
        self.assertEqual(model.get_completion_cost(), self.provider.cost_per_1k_tokens_completion)


class AIConfigModelTest(TestCase):
    """Test AIConfig model"""
    
    def setUp(self):
        self.provider = AIProvider.objects.create(
            name='Test Provider',
            cost_per_1k_tokens_prompt=Decimal('0.001'),
            cost_per_1k_tokens_completion=Decimal('0.002'),
        )
        self.model = AIModel.objects.create(
            provider=self.provider,
            name='test-model',
            display_name='Test Model',
        )
    
    def test_create_config(self):
        """Test creating an AI config"""
        config = AIConfig.objects.create(
            temperature=0.7,
            top_p=1.0,
            max_tokens=3000,
            daily_budget=Decimal('10.0'),
            monthly_budget=Decimal('300.0'),
            default_provider=self.provider,
            default_model=self.model,
            is_active=True
        )
        self.assertEqual(config.temperature, 0.7)
        self.assertEqual(config.daily_budget, Decimal('10.0'))
        self.assertTrue(config.is_active)
    
    def test_singleton_behavior(self):
        """Test that only one config can be active"""
        config1 = AIConfig.objects.create(
            default_provider=self.provider,
            default_model=self.model,
            is_active=True
        )
        config2 = AIConfig.objects.create(
            default_provider=self.provider,
            default_model=self.model,
            is_active=True
        )
        # Refresh config1 from database
        config1.refresh_from_db()
        # config1 should now be inactive
        self.assertFalse(config1.is_active)
        self.assertTrue(config2.is_active)
    
    def test_model_provider_validation(self):
        """Test that model must belong to provider"""
        other_provider = AIProvider.objects.create(name='Other Provider')
        other_model = AIModel.objects.create(
            provider=other_provider,
            name='other-model',
            display_name='Other Model'
        )
        
        config = AIConfig(
            default_provider=self.provider,
            default_model=other_model,
            is_active=True
        )
        with self.assertRaises(ValidationError):
            config.clean()


class PromptTemplateModelTest(TestCase):
    """Test PromptTemplate model"""
    
    def test_create_template(self):
        """Test creating a prompt template"""
        template = PromptTemplate.objects.create(
            slug='test-template',
            title='Test Template',
            category='other',
            content='This is a test prompt with {placeholder}',
            description='A test template',
            is_active=True
        )
        self.assertEqual(template.slug, 'test-template')
        self.assertTrue(template.is_active)
        self.assertIn('{placeholder}', template.content)


class AIUsageLogModelTest(TestCase):
    """Test AIUsageLog model"""
    
    def test_create_log(self):
        """Test creating a usage log"""
        log = AIUsageLog.objects.create(
            provider='OpenAI',
            model='gpt-4o-mini',
            prompt_slug='test-prompt',
            tokens_prompt=100,
            tokens_completion=50,
            cost=Decimal('0.0001'),
            latency_ms=1500,
            success=True,
            request_id='test-123'
        )
        self.assertEqual(log.provider, 'OpenAI')
        self.assertEqual(log.model, 'gpt-4o-mini')
        self.assertTrue(log.success)
        self.assertEqual(log.tokens_prompt, 100)


class LoaderFunctionsTest(TestCase):
    """Test loader functions"""
    
    def setUp(self):
        # Use or create provider (don't duplicate)
        self.provider, _ = AIProvider.objects.get_or_create(
            name='TestOpenAI',
            defaults={
                'cost_per_1k_tokens_prompt': Decimal('0.001'),
                'cost_per_1k_tokens_completion': Decimal('0.002'),
            }
        )
        self.model, _ = AIModel.objects.get_or_create(
            provider=self.provider,
            name='test-gpt-4o-mini',
            defaults={
                'display_name': 'Test GPT-4o Mini',
            }
        )
        # Deactivate any existing configs from data migration
        AIConfig.objects.all().update(is_active=False)
        self.config = AIConfig.objects.create(
            temperature=0.3,
            daily_budget=Decimal('5.0'),
            monthly_budget=Decimal('150.0'),
            default_provider=self.provider,
            default_model=self.model,
            is_active=True
        )
    
    def test_get_ai_config(self):
        """Test get_ai_config returns active config"""
        config = get_ai_config()
        self.assertEqual(config['temperature'], 0.3)
        self.assertEqual(config['default_provider'], 'TestOpenAI')
        self.assertEqual(config['default_model'], 'test-gpt-4o-mini')
        self.assertEqual(config['daily_budget'], 5.0)
    
    def test_get_prompt(self):
        """Test get_prompt returns template content"""
        PromptTemplate.objects.create(
            slug='test-prompt',
            title='Test Prompt',
            category='other',
            content='Test content with {variable}',
            is_active=True
        )
        prompt = get_prompt('test-prompt')
        self.assertIsNotNone(prompt)
        self.assertIn('{variable}', prompt)
    
    def test_get_prompt_inactive(self):
        """Test get_prompt returns None for inactive template"""
        PromptTemplate.objects.create(
            slug='inactive-prompt',
            title='Inactive Prompt',
            category='other',
            content='Inactive content',
            is_active=False
        )
        prompt = get_prompt('inactive-prompt')
        self.assertIsNone(prompt)
    
    def test_log_usage(self):
        """Test log_usage creates log entry"""
        initial_count = AIUsageLog.objects.count()
        log_usage(
            provider='TestOpenAI',
            model='test-gpt-4o-mini',
            prompt_slug='test-prompt',
            tokens_prompt=100,
            tokens_completion=50,
            cost=0.0001,
            latency_ms=1000,
            success=True,
            request_id='test-456'
        )
        self.assertEqual(AIUsageLog.objects.count(), initial_count + 1)
        log = AIUsageLog.objects.latest('created_at')
        self.assertEqual(log.provider, 'TestOpenAI')
        self.assertEqual(log.request_id, 'test-456')
    
    def test_check_budget(self):
        """Test check_budget returns correct status"""
        allowed, info = check_budget()
        self.assertTrue(allowed)
        self.assertEqual(info['daily_budget'], 5.0)
        self.assertEqual(info['monthly_budget'], 150.0)
        self.assertLessEqual(info['daily_spent'], info['daily_budget'])
    
    def test_calculate_cost(self):
        """Test calculate_cost computes correct cost"""
        cost = calculate_cost('TestOpenAI', 'test-gpt-4o-mini', 1000, 500)
        # (1000/1000 * 0.001) + (500/1000 * 0.002) = 0.001 + 0.001 = 0.002
        expected_cost = 0.002
        self.assertAlmostEqual(cost, expected_cost, places=6)

#!/usr/bin/env python
"""
Example usage of ai_config loader functions

This script demonstrates how to integrate the ai_config app
into existing scraper modules.
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'telis.settings')
django.setup()

from ai_config.loader import (
    get_ai_config,
    get_prompt,
    log_usage,
    check_budget,
    calculate_cost
)


def main():
    print("=" * 60)
    print("AI Config Integration Example")
    print("=" * 60)
    
    # 1. Get active configuration
    print("\n1. Getting active AI configuration...")
    config = get_ai_config()
    print(f"   Provider: {config['default_provider']}")
    print(f"   Model: {config['default_model_display']}")
    print(f"   Temperature: {config['temperature']}")
    print(f"   Max Tokens: {config['max_tokens']}")
    print(f"   Daily Budget: €{config['daily_budget']}")
    print(f"   Monthly Budget: €{config['monthly_budget']}")
    
    # 2. Check budget before making request
    print("\n2. Checking budget...")
    allowed, budget_info = check_budget()
    print(f"   Request allowed: {allowed}")
    print(f"   Daily spent: €{budget_info['daily_spent']:.6f}")
    print(f"   Daily remaining: €{budget_info['daily_remaining']:.6f}")
    print(f"   Monthly spent: €{budget_info['monthly_spent']:.6f}")
    print(f"   Monthly remaining: €{budget_info['monthly_remaining']:.6f}")
    
    if not allowed:
        print("   WARNING: Budget exceeded! Cannot make AI request.")
        return
    
    # 3. Get a prompt template
    print("\n3. Loading prompt template...")
    template = get_prompt('lead_extraction')
    if template:
        print(f"   Template loaded: lead_extraction")
        print(f"   Preview: {template[:100]}...")
        
        # Fill in the template
        example_content = """
        John Doe
        Senior Sales Manager
        Acme Corp
        Email: john.doe@acme.com
        Phone: +49 173 123 4567
        Location: Düsseldorf, NRW
        """
        prompt = template.format(content=example_content)
        print(f"   Filled prompt length: {len(prompt)} characters")
    else:
        print("   Template not found")
    
    # 4. Calculate expected cost
    print("\n4. Calculating expected cost...")
    prompt_tokens = 150
    completion_tokens = 75
    cost = calculate_cost(
        config['default_provider'],
        config['default_model'],
        prompt_tokens,
        completion_tokens
    )
    print(f"   Prompt tokens: {prompt_tokens}")
    print(f"   Completion tokens: {completion_tokens}")
    print(f"   Estimated cost: €{cost:.6f}")
    
    # 5. Simulate AI request and log usage
    print("\n5. Simulating AI request and logging usage...")
    # In real code, this would be an actual API call
    log_usage(
        provider=config['default_provider'],
        model=config['default_model'],
        prompt_slug='lead_extraction',
        tokens_prompt=prompt_tokens,
        tokens_completion=completion_tokens,
        cost=cost,
        latency_ms=1250,
        success=True,
        request_id='example-001',
        metadata={
            'example': True,
            'source': 'integration_example.py'
        }
    )
    print("   Usage logged successfully")
    
    # 6. Check budget again after logging
    print("\n6. Checking budget after request...")
    allowed, budget_info = check_budget()
    print(f"   Daily spent: €{budget_info['daily_spent']:.6f}")
    print(f"   Daily remaining: €{budget_info['daily_remaining']:.6f}")
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    main()

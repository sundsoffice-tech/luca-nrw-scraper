#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example: ML-Enhanced Lead Extraction and Scoring

This demonstrates how to use the new ML components for improved lead quality.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stream2_extraction_layer.extraction_enhanced import extract_with_multi_tier_fallback
from stream3_scoring_layer.scoring_enhanced import compute_score_v2
from stream3_scoring_layer.feedback_loop import get_feedback_system, FeedbackEntry


async def demo_ml_extraction():
    """Demonstrates ML-enhanced extraction."""
    print("=" * 70)
    print("DEMO: ML-Enhanced Lead Extraction")
    print("=" * 70)
    
    # Sample lead data
    html = """
    <div class="contact-info">
        <h3>Ihr Ansprechpartner</h3>
        <p>Herr Max Mustermann</p>
        <p>Vertriebsleiter</p>
        <p>Email: max.mustermann@versicherung-nrw.de</p>
        <p>Telefon: +49 175 1234567</p>
    </div>
    """
    
    text = "Wir sind ein führender Versicherungsmakler in NRW. " \
           "Kontaktieren Sie unseren Vertriebsleiter Max Mustermann."
    
    url = "https://versicherung-nrw.de/kontakt"
    company = "Versicherung NRW GmbH"
    
    # Extract with ML enhancement
    result = await extract_with_multi_tier_fallback(html, text, url, company)
    
    print("\n📊 Extraction Results:")
    print(f"  Name: {result.get('name')}")
    print(f"  Role: {result.get('rolle')}")
    print(f"  Email: {result.get('email')}")
    print(f"  Email Quality: {result.get('email_quality', 'N/A')}")
    print(f"  Email Category: {result.get('email_category', 'N/A')}")
    print(f"  Confidence: {result.get('confidence', 0):.2f}")
    print(f"  Method: {result.get('extraction_method')}")
    
    return result


def demo_ml_scoring():
    """Demonstrates ML-enhanced scoring with feedback."""
    print("\n" + "=" * 70)
    print("DEMO: Dynamic Scoring with Feedback Loop")
    print("=" * 70)
    
    # Initialize feedback system
    feedback_system = get_feedback_system("/tmp/demo_feedback.db")
    
    # Test leads
    leads = [
        {
            "id": 1,
            "name": "Max Mustermann",
            "email": "max.mustermann@firma-nrw.de",
            "telefon": "+491751234567",
            "phone_type": "mobile",
            "industry": "versicherung",
            "region": "NRW",
        },
        {
            "id": 2,
            "name": "Julia Schmidt",
            "email": "jobs@stepstone.de",
            "telefon": "+491601234567",
            "industry": "",
            "region": "",
        },
        {
            "id": 3,
            "name": "Peter Müller",
            "email": "p.mueller@gmail.com",
            "telefon": "+491771234567",
            "phone_type": "mobile",
            "industry": "energie",
            "region": "NRW",
        },
    ]
    
    print("\n📊 Lead Scores (without feedback):")
    for lead in leads:
        score = compute_score_v2("", "https://example.com", lead, use_dynamic_scoring=False)
        print(f"  Lead {lead['id']}: {score} points")
        lead['score_static'] = score
    
    # Simulate feedback
    print("\n💬 Simulating user feedback...")
    
    # Lead 1: High quality, successful conversion
    feedback_system.record_feedback(FeedbackEntry(
        lead_id=1,
        feedback_type='conversion',
        rating=0.9,
        notes='Excellent lead, converted successfully',
        metadata={
            'email_domain': 'firma-nrw.de',
            'industry': 'versicherung',
            'region': 'NRW',
        }
    ))
    
    # Lead 2: Low quality, portal email
    feedback_system.record_feedback(FeedbackEntry(
        lead_id=2,
        feedback_type='quality',
        rating=0.2,
        notes='Portal email, no real contact',
        metadata={
            'email_domain': 'stepstone.de',
            'industry': '',
        }
    ))
    
    # Lead 3: Good quality
    feedback_system.record_feedback(FeedbackEntry(
        lead_id=3,
        feedback_type='quality',
        rating=0.8,
        notes='Good lead, personal email',
        metadata={
            'email_domain': 'gmail.com',
            'industry': 'energie',
        }
    ))
    
    print("\n📊 Lead Scores (with dynamic scoring):")
    for lead in leads:
        score = compute_score_v2("", "https://example.com", lead, use_dynamic_scoring=True)
        score_diff = score - lead['score_static']
        adjustment_symbol = "↑" if score_diff > 0 else "↓" if score_diff < 0 else "="
        print(f"  Lead {lead['id']}: {score} points ({adjustment_symbol} {abs(score_diff):.0f} from feedback)")
    
    # Show quality metrics
    print("\n📈 Quality Metrics:")
    metrics = feedback_system.get_quality_metrics(days=7)
    print(f"  Average Rating: {metrics.avg_rating:.2f}")
    print(f"  Positive Rate: {metrics.positive_rate:.1%}")
    print(f"  Total Feedback: {metrics.total_feedback}")


async def main():
    """Run all demos."""
    print("\n🚀 ML-Enhanced Lead Processing Demo")
    print("=" * 70)
    
    # Demo 1: ML Extraction
    await demo_ml_extraction()
    
    # Demo 2: Dynamic Scoring
    demo_ml_scoring()
    
    print("\n" + "=" * 70)
    print("✅ Demo Complete!")
    print("=" * 70)
    print("\nFor more details, see: docs/ML_ENHANCED_SYSTEM.md")


if __name__ == "__main__":
    asyncio.run(main())

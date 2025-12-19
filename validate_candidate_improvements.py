#!/usr/bin/env python3
"""
Validation script to demonstrate the candidate mode improvements.
Shows how the system now correctly identifies job-seeking candidates.
"""

from scriptname import (
    is_candidate_seeking_job,
    is_job_advertisement,
    is_garbage_context,
    has_nrw_signal,
)


def test_case(description, text, title="", url=""):
    """Run a test case and display results."""
    print(f"\n{'='*80}")
    print(f"Test: {description}")
    print(f"{'='*80}")
    print(f"Text: {text}")
    if title:
        print(f"Title: {title}")
    if url:
        print(f"URL: {url}")
    
    is_candidate = is_candidate_seeking_job(text, title, url)
    is_job_ad = is_job_advertisement(text, title, "")
    is_garbage, garbage_reason = is_garbage_context(text, url, title, "")
    has_nrw = has_nrw_signal(text + " " + title)
    
    print(f"\nResults:")
    print(f"  ✓ Is Candidate Seeking Job: {is_candidate}")
    print(f"  ✓ Is Job Advertisement: {is_job_ad}")
    print(f"  ✓ Is Garbage Context: {is_garbage} {f'({garbage_reason})' if is_garbage else ''}")
    print(f"  ✓ Has NRW Signal: {has_nrw}")
    
    # Determine if this would be blocked or allowed
    if is_candidate and not is_job_ad and not is_garbage:
        print(f"\n  ✅ RESULT: ALLOWED - This candidate would be found!")
    else:
        print(f"\n  ❌ RESULT: BLOCKED - This would be filtered out")
    
    return is_candidate and not is_job_ad and not is_garbage


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                  CANDIDATE MODE IMPROVEMENTS VALIDATION                     ║
║                                                                              ║
║  Demonstrating fixes to prevent false blocking of job-seeking candidates   ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
    
    test_cases = [
        # Cases that should PASS (candidates seeking jobs)
        {
            "description": "Kleinanzeigen Stellengesuch - should PASS",
            "text": "Ich suche neuen Job im Vertrieb. 10 Jahre Erfahrung. Mobil: 0176-12345678",
            "title": "Stellengesuch: Vertriebsmitarbeiter NRW",
            "url": "https://kleinanzeigen.de/s-stellengesuche/vertrieb-123",
        },
        {
            "description": "LinkedIn Open to Work - should PASS",
            "text": "Experienced sales manager, open to work in NRW region",
            "title": "Max Mustermann | Sales Manager | #OpenToWork",
            "url": "https://linkedin.com/in/max-mustermann",
        },
        {
            "description": "Xing Profile offen für Angebote - should PASS",
            "text": "Offen für neue Angebote im Vertrieb. 8 Jahre B2B Sales Erfahrung.",
            "title": "Anna Schmidt - Vertriebsleiterin Düsseldorf",
            "url": "https://xing.com/profile/Anna_Schmidt",
        },
        {
            "description": "Minijob Search - should PASS",
            "text": "Ich suche Minijobs im Verkauf",
            "title": "Suche Minijob Verkäuferin",
            "url": "https://kleinanzeigen.de/s-stellengesuche/minijob-456",
        },
        {
            "description": "Facebook Job Search - should PASS",
            "text": "Suche neue Herausforderung im Außendienst NRW. Kontakt: 0176-98765432",
            "title": "Jobsuche Vertrieb",
            "url": "https://facebook.com/posts/123456",
        },
        
        # Cases that should FAIL (company job postings)
        {
            "description": "Company Job Posting - should FAIL",
            "text": "Wir suchen Vertriebsmitarbeiter (m/w/d) für unser Team in Düsseldorf",
            "title": "Sales Manager (m/w/d) gesucht",
            "url": "https://company.de/karriere/jobs/sales-123",
        },
        {
            "description": "Company Stellenanzeige - should FAIL",
            "text": "Stellenanzeige: Außendienstmitarbeiter gesucht. Wir bieten attraktives Gehalt.",
            "title": "Job: Außendienst (m/w/d)",
            "url": "https://company.de/jobs/aussendienst",
        },
    ]
    
    passed = 0
    total = len(test_cases)
    
    for test in test_cases:
        should_pass = "should PASS" in test["description"]
        result = test_case(
            test["description"],
            test["text"],
            test.get("title", ""),
            test.get("url", "")
        )
        
        if should_pass == result:
            passed += 1
        else:
            print(f"\n  ⚠️  WARNING: Unexpected result!")
    
    print(f"\n\n{'='*80}")
    print(f"SUMMARY: {passed}/{total} test cases behaved as expected")
    print(f"{'='*80}\n")
    
    if passed == total:
        print("✅ All improvements are working correctly!")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) had unexpected behavior")
        return 1


if __name__ == "__main__":
    exit(main())

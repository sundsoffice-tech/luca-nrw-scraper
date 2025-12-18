import pytest
from scriptname import is_candidate_url


def test_is_candidate_url_positive():
    """Test that candidate URLs are correctly identified."""
    # Kleinanzeigen Stellengesuche
    assert is_candidate_url("https://www.kleinanzeigen.de/s-stellengesuche/vertrieb/k0") is True
    assert is_candidate_url("https://kleinanzeigen.de/s-stellengesuche/verkauf/k0") is True
    
    # Other classified ads
    assert is_candidate_url("https://www.markt.de/stellengesuche/vertrieb-123.html") is True
    assert is_candidate_url("https://quoka.de/stellengesuche/sales-456") is True
    
    # LinkedIn profiles
    assert is_candidate_url("https://www.linkedin.com/in/john-doe-123456") is True
    assert is_candidate_url("https://de.linkedin.com/in/max-mustermann") is True
    
    # Xing profiles
    assert is_candidate_url("https://www.xing.com/profile/Max_Mustermann") is True
    
    # Freelancer portals
    assert is_candidate_url("https://www.freelancermap.de/freelancer/12345-vertrieb") is True
    assert is_candidate_url("https://freelance.de/freelancer/vertrieb-experte") is True
    assert is_candidate_url("https://www.gulp.de/freelancer/sales-123") is True
    
    # Social media groups
    assert is_candidate_url("https://www.facebook.com/groups/vertrieb-jobs-nrw") is True
    assert is_candidate_url("https://t.me/vertrieb_jobs_gruppe") is True
    assert is_candidate_url("https://chat.whatsapp.com/invite123") is True
    
    # Forums
    assert is_candidate_url("https://www.reddit.com/r/arbeitsleben/comments/abc123") is True
    assert is_candidate_url("https://www.gutefrage.net/frage/wie-finde-ich-vertriebsjob") is True
    
    # Instagram should be uncertain (too broad - could be influencers, businesses, etc.)
    assert is_candidate_url("https://www.instagram.com/user123") is None


def test_is_candidate_url_negative():
    """Test that non-candidate URLs are correctly rejected."""
    # Job boards (Stellenangebote, not Stellengesuche)
    assert is_candidate_url("https://www.stepstone.de/jobs/vertrieb") is False
    assert is_candidate_url("https://de.indeed.com/jobs?q=vertrieb") is False
    assert is_candidate_url("https://www.monster.de/jobs/search") is False
    
    # Job postings on LinkedIn/Xing
    assert is_candidate_url("https://www.linkedin.com/jobs/view/123456") is False
    assert is_candidate_url("https://www.xing.com/jobs/dusseldorf-sales-123") is False
    
    # Company pages
    assert is_candidate_url("https://www.example.com/karriere/stellenangebote") is False
    assert is_candidate_url("https://www.company.de/jobs/vertrieb") is False
    assert is_candidate_url("https://www.linkedin.com/company/example-gmbh") is False
    
    # Company contact/imprint pages
    assert is_candidate_url("https://www.company.de/impressum") is False
    assert is_candidate_url("https://www.example.com/kontakt") is False
    assert is_candidate_url("https://www.firm.de/about-us") is False
    
    # Job boards
    assert is_candidate_url("https://www.jobboerse.de/vertrieb") is False


def test_is_candidate_url_uncertain():
    """Test URLs that need further analysis."""
    # Generic pages that could be either
    assert is_candidate_url("https://www.example.com/blog/vertrieb-tipps") is None
    assert is_candidate_url("https://www.company.de/news/artikel-123") is None
    assert is_candidate_url("https://www.somesite.de/page.html") is None
    
    # Empty or None URL
    assert is_candidate_url("") is None
    assert is_candidate_url(None) is None


def test_is_candidate_url_case_insensitive():
    """Test that URL matching is case-insensitive."""
    assert is_candidate_url("https://www.KLEINANZEIGEN.de/s-STELLENGESUCHE/vertrieb") is True
    assert is_candidate_url("https://WWW.LINKEDIN.COM/IN/john-doe") is True
    assert is_candidate_url("https://WWW.STEPSTONE.DE/JOBS/vertrieb") is False
    assert is_candidate_url("https://www.company.de/IMPRESSUM") is False


def test_is_candidate_url_complex_paths():
    """Test URLs with complex paths."""
    # Candidate URL with query parameters
    assert is_candidate_url("https://kleinanzeigen.de/s-stellengesuche/nrw/vertrieb/k0?q=sales") is True
    
    # Job posting URL with fragments
    assert is_candidate_url("https://www.company.de/karriere/jobs/vertrieb#apply") is False
    
    # LinkedIn profile with additional path
    assert is_candidate_url("https://www.linkedin.com/in/max-mustermann/details/experience/") is True

# -*- coding: utf-8 -*-
"""
Webapp default settings for candidate-focused mode.
"""

WEBAPP_DEFAULTS = {
    "default_mode": "candidates",
    "show_employers": False,
    "show_job_ads": False,
    "require_mobile_phone": True,
    "require_real_name": True,
    "min_score": 40,
    "priority_source_types": [
        "stellengesuch_kleinanzeigen",
        "linkedin_opentowork",
        "xing_offen",
        "telegram_vertrieb",
    ],
    "preferred_industries": ["solar", "telekom", "versicherung", "energie"],
    "include_hidden_gems": True,
    "hidden_gems_min_confidence": 60,
    "default_view": "active_jobseekers",
    "columns_visible": ["name", "telefon", "source_type", "skills", "availability", "score"],
}

"""KI-gestützte Email-Generierung"""
import os
from typing import Dict, List, Optional
from ai_config.loader import get_ai_config, get_prompt, log_usage, check_budget


# Default Prompt für Email-Generierung
DEFAULT_EMAIL_PROMPT = """Du bist ein professioneller Email-Texter für Recruiting und Vertrieb.

Erstelle ein Email-Template mit folgenden Anforderungen:
- Kategorie: {category}
- Kontext: {context}
- Tonalität: {tone}
- Sprache: {language}

Das Template soll Variablen in der Form {{variable}} enthalten.
Verwende mindestens diese Variablen: {{name}}, {{email}}

Antworte im folgenden JSON-Format:
{{
    "subject": "Betreff mit {{variablen}}",
    "html_content": "<p>HTML-Inhalt mit {{variablen}}</p>",
    "text_content": "Plain-Text Version",
    "variables_used": ["name", "email", "company"]
}}
"""


def generate_email_template(
    category: str,
    context: str,
    tone: str = "professional",
    language: str = "de"
) -> dict:
    """
    Generiert ein komplettes Email-Template mit KI.
    
    Args:
        category: Template-Kategorie (welcome, follow_up, etc.)
        context: Beschreibung des Anwendungsfalls
        tone: Tonalität (professional, friendly, formal)
        language: Sprache (de, en)
    
    Returns:
        dict: {subject, html_content, text_content, variables_used}
    
    Raises:
        Exception: Wenn Budget überschritten oder API-Fehler
    """
    # Budget prüfen
    allowed, budget_info = check_budget()
    if not allowed:
        raise Exception(
            f"Budget überschritten. Täglich verbleibend: {budget_info['daily_remaining']:.2f} EUR, "
            f"Monatlich verbleibend: {budget_info['monthly_remaining']:.2f} EUR"
        )
    
    # Config laden
    config = get_ai_config()
    
    # Prompt laden oder Default verwenden
    prompt_template = get_prompt('email_generation') or DEFAULT_EMAIL_PROMPT
    
    # Prompt formatieren
    prompt = prompt_template.format(
        category=category,
        context=context,
        tone=tone,
        language=language
    )
    
    # Prüfe ob OpenAI API Key vorhanden ist
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        raise Exception("OPENAI_API_KEY nicht in Umgebungsvariablen gesetzt")
    
    # OpenAI Call (mit Budget-Logging)
    try:
        import openai
        import json
        import time
        
        client = openai.OpenAI(api_key=api_key)
        
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=config.get('default_model', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": "Du bist ein professioneller Email-Texter."},
                {"role": "user", "content": prompt}
            ],
            temperature=config.get('temperature', 0.3),
            max_tokens=config.get('max_tokens', 4000),
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Token-Verbrauch und Kosten
        tokens_prompt = response.usage.prompt_tokens
        tokens_completion = response.usage.completion_tokens
        
        # Kosten berechnen (vereinfachte Annahme: 0.00015 EUR pro 1K tokens prompt, 0.0006 EUR per 1K completion)
        cost = (tokens_prompt / 1000.0) * 0.00015 + (tokens_completion / 1000.0) * 0.0006
        
        # Usage loggen
        log_usage(
            provider=config.get('default_provider', 'OpenAI'),
            model=config.get('default_model', 'gpt-4o-mini'),
            prompt_slug='email_generation',
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            cost=cost,
            latency_ms=latency_ms,
            success=True
        )
        
        # Response parsen
        content = response.choices[0].message.content.strip()
        
        # JSON extrahieren (falls in Markdown Code Block)
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        result = json.loads(content)
        
        return result
        
    except Exception as e:
        # Fehler loggen
        log_usage(
            provider=config.get('default_provider', 'OpenAI'),
            model=config.get('default_model', 'gpt-4o-mini'),
            prompt_slug='email_generation',
            success=False,
            error_message=str(e)
        )
        raise Exception(f"Fehler bei der KI-Generierung: {str(e)}")


def improve_email_text(
    text: str,
    improvement_type: str = "clarity"  # clarity, persuasion, brevity
) -> str:
    """
    Verbessert bestehenden Email-Text mit KI.
    
    Args:
        text: Der zu verbessernde Text
        improvement_type: Art der Verbesserung (clarity, persuasion, brevity)
    
    Returns:
        str: Verbesserter Text
    
    Raises:
        Exception: Wenn Budget überschritten oder API-Fehler
    """
    # Budget prüfen
    allowed, budget_info = check_budget()
    if not allowed:
        raise Exception(f"Budget überschritten: {budget_info}")
    
    # Config laden
    config = get_ai_config()
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        raise Exception("OPENAI_API_KEY nicht gesetzt")
    
    improvement_instructions = {
        'clarity': 'Mache den Text klarer und verständlicher, ohne die Bedeutung zu verändern.',
        'persuasion': 'Mache den Text überzeugender und ansprechender.',
        'brevity': 'Kürze den Text, behalte aber alle wichtigen Informationen.'
    }
    
    prompt = f"{improvement_instructions.get(improvement_type, improvement_instructions['clarity'])}\n\nText:\n{text}"
    
    try:
        import openai
        import time
        
        client = openai.OpenAI(api_key=api_key)
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=config.get('default_model', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": "Du bist ein professioneller Email-Texter."},
                {"role": "user", "content": prompt}
            ],
            temperature=config.get('temperature', 0.3),
            max_tokens=config.get('max_tokens', 4000),
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        tokens_prompt = response.usage.prompt_tokens
        tokens_completion = response.usage.completion_tokens
        cost = (tokens_prompt / 1000.0) * 0.00015 + (tokens_completion / 1000.0) * 0.0006
        
        log_usage(
            provider=config.get('default_provider', 'OpenAI'),
            model=config.get('default_model', 'gpt-4o-mini'),
            prompt_slug='email_improvement',
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            cost=cost,
            latency_ms=latency_ms,
            success=True
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        log_usage(
            provider=config.get('default_provider', 'OpenAI'),
            model=config.get('default_model', 'gpt-4o-mini'),
            prompt_slug='email_improvement',
            success=False,
            error_message=str(e)
        )
        raise Exception(f"Fehler bei der Text-Verbesserung: {str(e)}")


def generate_subject_lines(
    content: str,
    count: int = 5
) -> List[str]:
    """
    Generiert mehrere Betreffzeilen-Vorschläge.
    
    Args:
        content: Email-Inhalt für den Kontext
        count: Anzahl der zu generierenden Betreffzeilen
    
    Returns:
        list: Liste von Betreffzeilen
    
    Raises:
        Exception: Wenn Budget überschritten oder API-Fehler
    """
    # Budget prüfen
    allowed, budget_info = check_budget()
    if not allowed:
        raise Exception(f"Budget überschritten: {budget_info}")
    
    config = get_ai_config()
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        raise Exception("OPENAI_API_KEY nicht gesetzt")
    
    prompt = f"""Basierend auf folgendem Email-Inhalt, generiere {count} verschiedene, ansprechende Betreffzeilen.
Die Betreffzeilen sollen kurz, prägnant und aufmerksamkeitserregend sein.

Email-Inhalt:
{content[:500]}

Antworte nur mit den Betreffzeilen, eine pro Zeile."""
    
    try:
        import openai
        import time
        
        client = openai.OpenAI(api_key=api_key)
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=config.get('default_model', 'gpt-4o-mini'),
            messages=[
                {"role": "system", "content": "Du bist ein kreativer Email-Marketing-Experte."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # Höhere Temperatur für mehr Kreativität
            max_tokens=500,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        tokens_prompt = response.usage.prompt_tokens
        tokens_completion = response.usage.completion_tokens
        cost = (tokens_prompt / 1000.0) * 0.00015 + (tokens_completion / 1000.0) * 0.0006
        
        log_usage(
            provider=config.get('default_provider', 'OpenAI'),
            model=config.get('default_model', 'gpt-4o-mini'),
            prompt_slug='subject_generation',
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            cost=cost,
            latency_ms=latency_ms,
            success=True
        )
        
        # Zeilen splitten und leere entfernen
        subjects = [line.strip() for line in response.choices[0].message.content.strip().split('\n') if line.strip()]
        
        # Entferne Nummerierung falls vorhanden (z.B. "1. ", "- ")
        import re
        subjects = [re.sub(r'^[\d\-\*\.]+\s*', '', s) for s in subjects]
        
        return subjects[:count]
        
    except Exception as e:
        log_usage(
            provider=config.get('default_provider', 'OpenAI'),
            model=config.get('default_model', 'gpt-4o-mini'),
            prompt_slug='subject_generation',
            success=False,
            error_message=str(e)
        )
        raise Exception(f"Fehler bei der Betreffzeilen-Generierung: {str(e)}")

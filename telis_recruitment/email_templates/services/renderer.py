"""Template-Rendering mit Variablen"""
import logging
import re
from typing import Dict, Any, List, Set

logger = logging.getLogger(__name__)


def render_template(template_str: str, variables: Dict[str, Any]) -> str:
    """
    Rendert einen Template-String mit den gegebenen Variablen.
    
    Args:
        template_str: Template-String mit {variablen}
        variables: Dictionary mit Variablen-Werten
    
    Returns:
        str: Gerenderter String
    
    Example:
        >>> render_template("Hallo {name}!", {"name": "Max"})
        "Hallo Max!"
    """
    if not template_str:
        return template_str
        
    try:
        # First extract what variables are in the template
        required_vars = extract_variables_from_template(template_str)
        
        # Check for missing variables and log warnings
        missing_vars = set(required_vars) - set(variables.keys())
        if missing_vars:
            logger.warning(
                f"Template rendering: Missing variables {missing_vars}. "
                f"Template will contain unreplaced placeholders."
            )
            # Use partial formatting - replace only available variables
            result = template_str
            for var_name, var_value in variables.items():
                result = result.replace('{' + var_name + '}', str(var_value))
            return result
        
        return template_str.format(**variables)
    except KeyError as e:
        logger.warning(f"Template rendering: Variable {e} not found in provided variables")
        return template_str
    except Exception as e:
        logger.error(f"Template rendering error: {e}")
        return template_str


def render_email_template(template, variables: Dict[str, Any]) -> Dict[str, str]:
    """
    Rendert ein komplettes Email-Template.
    
    Args:
        template: EmailTemplate model instance
        variables: Dictionary mit Variablen-Werten
    
    Returns:
        dict: {
            'subject': gerenderter Betreff,
            'html_content': gerenderter HTML-Inhalt,
            'text_content': gerenderter Text-Inhalt
        }
    
    Example:
        >>> from email_templates.models import EmailTemplate
        >>> template = EmailTemplate.objects.get(slug='welcome')
        >>> vars = {'name': 'Max', 'company': 'Acme Inc'}
        >>> result = render_email_template(template, vars)
        >>> print(result['subject'])
    """
    return {
        'subject': render_template(template.subject, variables),
        'html_content': render_template(template.html_content, variables),
        'text_content': render_template(template.text_content, variables),
    }


def extract_variables_from_template(template_str: str) -> list:
    """
    Extrahiert alle Variablen aus einem Template-String.
    
    Args:
        template_str: Template-String mit {variablen}
    
    Returns:
        list: Liste der gefundenen Variablen-Namen
    
    Example:
        >>> extract_variables_from_template("Hallo {name}, von {company}!")
        ['name', 'company']
    """
    if not template_str:
        return []
    # Findet alle {variable} Muster
    pattern = r'\{(\w+)\}'
    matches = re.findall(pattern, template_str)
    # Entferne Duplikate und sortiere
    return sorted(list(set(matches)))


def get_template_variables(template) -> list:
    """
    Gibt alle Variablen zurück, die in einem Template verwendet werden.
    
    Args:
        template: EmailTemplate model instance
    
    Returns:
        list: Liste aller verwendeten Variablen
    """
    variables = set()
    variables.update(extract_variables_from_template(template.subject))
    variables.update(extract_variables_from_template(template.html_content))
    if template.text_content:
        variables.update(extract_variables_from_template(template.text_content))
    
    return sorted(list(variables))


def get_sample_variables() -> Dict[str, str]:
    """
    Gibt Beispiel-Variablen für Vorschau zurück.
    
    Returns:
        dict: Dictionary mit Standard-Beispielwerten
    """
    return {
        'name': 'Max Mustermann',
        'email': 'max.mustermann@example.com',
        'company': 'Musterfirma GmbH',
        'telefon': '+49 123 456789',
        'role': 'Vertriebsleiter',
        'location': 'Berlin',
        'first_name': 'Max',
        'last_name': 'Mustermann',
        'date': '18.01.2026',
        'time': '14:30',
    }

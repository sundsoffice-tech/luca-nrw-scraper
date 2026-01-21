"""
Error type definitions for scraper control.

Provides structured error types and contextual information for better UI feedback.
"""

from enum import Enum
from typing import Dict, Any, Optional


class ScraperErrorType(str, Enum):
    """
    Enum for different scraper error types.
    Enables the UI to provide specific feedback based on error category.
    """
    # Configuration errors
    CONFIG_ERROR = "CONFIG_ERROR"
    CONFIG_FILE_MISSING = "CONFIG_FILE_MISSING"
    CONFIG_INVALID = "CONFIG_INVALID"
    
    # Script errors
    SCRIPT_NOT_FOUND = "SCRIPT_NOT_FOUND"
    SCRIPT_PERMISSION_DENIED = "SCRIPT_PERMISSION_DENIED"
    
    # Process errors
    PROCESS_START_FAILED = "PROCESS_START_FAILED"
    PROCESS_CRASH = "PROCESS_CRASH"
    PROCESS_EARLY_EXIT = "PROCESS_EARLY_EXIT"
    
    # Circuit breaker
    CIRCUIT_BREAKER_OPEN = "CIRCUIT_BREAKER_OPEN"
    
    # Dependency errors
    MISSING_DEPENDENCY = "MISSING_DEPENDENCY"
    PYTHON_VERSION_ERROR = "PYTHON_VERSION_ERROR"
    
    # Runtime errors
    RATE_LIMIT_ERROR = "RATE_LIMIT_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    
    # Permission errors
    PERMISSION_DENIED = "PERMISSION_DENIED"
    FILE_ACCESS_ERROR = "FILE_ACCESS_ERROR"
    
    # Generic
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    ALREADY_RUNNING = "ALREADY_RUNNING"
    NOT_RUNNING = "NOT_RUNNING"


class ErrorContext:
    """
    Provides detailed error context and recovery suggestions.
    """
    
    @staticmethod
    def get_error_info(
        error_type: ScraperErrorType,
        details: Optional[str] = None,
        component: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive error information for a given error type.
        
        Args:
            error_type: The type of error
            details: Additional details about the error
            component: The component that failed
            
        Returns:
            Dictionary with error_type, error_message, and recovery_action
        """
        error_messages = {
            ScraperErrorType.CONFIG_ERROR: {
                "message": "Konfigurationsfehler: Die Scraper-Konfiguration konnte nicht geladen werden.",
                "recovery": "Überprüfen Sie die Scraper-Konfiguration in den Einstellungen."
            },
            ScraperErrorType.CONFIG_FILE_MISSING: {
                "message": "Konfigurationsdatei fehlt: Die erforderliche Konfigurationsdatei wurde nicht gefunden.",
                "recovery": "Erstellen Sie eine neue Konfiguration oder stellen Sie die Standardkonfiguration wieder her."
            },
            ScraperErrorType.CONFIG_INVALID: {
                "message": "Ungültige Konfiguration: Die Konfigurationsdatei enthält ungültige Werte.",
                "recovery": "Überprüfen Sie die Konfiguration auf Syntaxfehler oder ungültige Werte."
            },
            ScraperErrorType.SCRIPT_NOT_FOUND: {
                "message": "Scraper-Skript nicht gefunden: Die Scraper-Hauptdatei konnte nicht gefunden werden.",
                "recovery": "Stellen Sie sicher, dass luca_scraper/cli.py oder scriptname.py existiert."
            },
            ScraperErrorType.SCRIPT_PERMISSION_DENIED: {
                "message": "Zugriff verweigert: Keine Berechtigung zum Ausführen des Scraper-Skripts.",
                "recovery": "Überprüfen Sie die Dateiberechtigungen des Scraper-Skripts."
            },
            ScraperErrorType.PROCESS_START_FAILED: {
                "message": "Prozessstart fehlgeschlagen: Der Scraper-Prozess konnte nicht gestartet werden.",
                "recovery": "Überprüfen Sie die Systemressourcen und Berechtigungen."
            },
            ScraperErrorType.PROCESS_CRASH: {
                "message": "Prozess abgestürzt: Der Scraper ist unerwartet beendet worden.",
                "recovery": "Überprüfen Sie die Logs auf detaillierte Fehlerinformationen."
            },
            ScraperErrorType.PROCESS_EARLY_EXIT: {
                "message": "Frühzeitiger Exit: Der Scraper wurde innerhalb von 5 Sekunden beendet.",
                "recovery": "Dies deutet auf einen Startup-Fehler hin. Überprüfen Sie die Logs und Dependencies."
            },
            ScraperErrorType.CIRCUIT_BREAKER_OPEN: {
                "message": "Circuit Breaker aktiv: Zu viele aufeinanderfolgende Fehler aufgetreten.",
                "recovery": "Warten Sie auf die automatische Wiederherstellung oder setzen Sie den Circuit Breaker manuell zurück."
            },
            ScraperErrorType.MISSING_DEPENDENCY: {
                "message": "Fehlende Abhängigkeit: Ein erforderliches Python-Modul fehlt.",
                "recovery": "Installieren Sie die fehlenden Dependencies mit 'pip install -r requirements.txt'."
            },
            ScraperErrorType.PYTHON_VERSION_ERROR: {
                "message": "Python-Versionsfehler: Die Python-Version ist inkompatibel.",
                "recovery": "Verwenden Sie Python 3.8 oder höher."
            },
            ScraperErrorType.RATE_LIMIT_ERROR: {
                "message": "Rate Limit erreicht: Die API-Anfragen wurden gedrosselt.",
                "recovery": "Reduzieren Sie die QPI (Queries Per Industry) oder warten Sie einige Minuten."
            },
            ScraperErrorType.CONNECTION_ERROR: {
                "message": "Verbindungsfehler: Netzwerkverbindung zum Ziel-Server fehlgeschlagen.",
                "recovery": "Überprüfen Sie die Internetverbindung und Firewall-Einstellungen."
            },
            ScraperErrorType.TIMEOUT_ERROR: {
                "message": "Timeout: Die Anfrage hat zu lange gedauert.",
                "recovery": "Überprüfen Sie die Netzwerkverbindung oder erhöhen Sie das Timeout."
            },
            ScraperErrorType.PERMISSION_DENIED: {
                "message": "Zugriff verweigert: Keine ausreichenden Berechtigungen.",
                "recovery": "Überprüfen Sie die Dateisystem- und Prozessberechtigungen."
            },
            ScraperErrorType.FILE_ACCESS_ERROR: {
                "message": "Dateizugriffsfehler: Eine erforderliche Datei konnte nicht gelesen/geschrieben werden.",
                "recovery": "Überprüfen Sie die Dateiberechtigungen und den verfügbaren Speicherplatz."
            },
            ScraperErrorType.ALREADY_RUNNING: {
                "message": "Scraper läuft bereits: Ein Scraper-Prozess ist bereits aktiv.",
                "recovery": "Stoppen Sie den laufenden Prozess, bevor Sie einen neuen starten."
            },
            ScraperErrorType.NOT_RUNNING: {
                "message": "Kein Scraper-Prozess läuft.",
                "recovery": "Starten Sie den Scraper zuerst, bevor Sie ihn stoppen."
            },
            ScraperErrorType.UNKNOWN_ERROR: {
                "message": "Unbekannter Fehler: Ein unerwarteter Fehler ist aufgetreten.",
                "recovery": "Überprüfen Sie die Logs für weitere Informationen."
            }
        }
        
        error_info = error_messages.get(error_type, error_messages[ScraperErrorType.UNKNOWN_ERROR])
        
        result = {
            "error_type": error_type.value,
            "error_message": error_info["message"],
            "recovery_action": error_info["recovery"]
        }
        
        if details:
            result["error_details"] = details
            
        if component:
            result["failed_component"] = component
            
        return result


def create_error_response(
    error_type: ScraperErrorType,
    details: Optional[str] = None,
    component: Optional[str] = None,
    status: str = "error",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized error response dictionary.
    
    Args:
        error_type: The type of error
        details: Additional details about the error
        component: The component that failed
        status: Status string (default: "error")
        **kwargs: Additional fields to include in response
        
    Returns:
        Dictionary with success=False and error information
    """
    error_info = ErrorContext.get_error_info(error_type, details, component)
    
    response = {
        "success": False,
        "status": status,
        **error_info,
        **kwargs
    }
    
    return response

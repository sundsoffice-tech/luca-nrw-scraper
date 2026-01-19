from django.db import models
from django.contrib.auth.models import User


class ReportSchedule(models.Model):
    """Geplante automatische Reports"""
    FREQUENCY_CHOICES = [
        ('daily', 'Täglich'),
        ('weekly', 'Wöchentlich'),
        ('monthly', 'Monatlich'),
    ]
    
    REPORT_TYPE_CHOICES = [
        ('lead_overview', 'Lead-Übersicht'),
        ('scraper_performance', 'Scraper-Performance'),
        ('conversion_funnel', 'Conversion-Funnel'),
        ('source_analysis', 'Quellen-Analyse'),
        ('cost_analysis', 'Kosten-Analyse'),
    ]
    
    name = models.CharField(max_length=255, verbose_name="Name")
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES, verbose_name="Report-Typ")
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, verbose_name="Häufigkeit")
    recipients = models.JSONField(default=list, verbose_name="Empfänger", help_text="Liste von Email-Adressen")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    last_run = models.DateTimeField(null=True, blank=True, verbose_name="Letzter Lauf")
    next_run = models.DateTimeField(null=True, blank=True, verbose_name="Nächster Lauf")
    created_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Erstellt von"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Report-Zeitplan"
        verbose_name_plural = "Report-Zeitpläne"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"


class ReportHistory(models.Model):
    """Generierte Reports Historie"""
    schedule = models.ForeignKey(
        ReportSchedule, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='history',
        verbose_name="Zeitplan"
    )
    report_type = models.CharField(max_length=50, verbose_name="Report-Typ")
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name="Generiert am")
    generated_by = models.ForeignKey(
        'auth.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Generiert von"
    )
    period_start = models.DateField(verbose_name="Zeitraum Start")
    period_end = models.DateField(verbose_name="Zeitraum Ende")
    data = models.JSONField(default=dict, verbose_name="Report-Daten")
    file_path = models.CharField(max_length=500, blank=True, verbose_name="Dateipfad")
    file_format = models.CharField(
        max_length=10, 
        blank=True,
        choices=[('pdf', 'PDF'), ('xlsx', 'Excel'), ('csv', 'CSV')],
        verbose_name="Dateiformat"
    )
    
    class Meta:
        verbose_name = "Report-Historie"
        verbose_name_plural = "Report-Historien"
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.report_type} - {self.generated_at.strftime('%d.%m.%Y %H:%M')}"

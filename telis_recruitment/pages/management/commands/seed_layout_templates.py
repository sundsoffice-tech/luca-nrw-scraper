"""Management command to seed flexible layout templates"""
from django.core.management.base import BaseCommand
from pages.models import PageTemplate


class Command(BaseCommand):
    help = 'Seed flexible layout templates (Landing, Contact, Sales, Info)'

    def handle(self, *args, **options):
        """Create or update flexible layout templates"""
        
        templates = [
            # Landing Page Template
            {
                'name': 'Moderne Landingpage',
                'slug': 'moderne-landingpage',
                'category': 'landing',
                'description': 'Vollständig anpassbare Landingpage mit Hero, Features, Testimonials und CTA',
                'html_json': {
                    'components': [
                        {
                            'tagName': 'section',
                            'attributes': {'class': 'hero-section', 'data-section': 'hero'},
                            'components': [
                                {
                                    'tagName': 'div',
                                    'attributes': {'class': 'container'},
                                    'components': [
                                        {
                                            'tagName': 'h1',
                                            'attributes': {'class': 'hero-title'},
                                            'components': [{'type': 'textnode', 'content': 'Willkommen zu Ihrer Landingpage'}]
                                        },
                                        {
                                            'tagName': 'p',
                                            'attributes': {'class': 'hero-subtitle'},
                                            'components': [{'type': 'textnode', 'content': 'Passen Sie jeden Bereich nach Ihren Wünschen an'}]
                                        },
                                        {
                                            'tagName': 'button',
                                            'attributes': {'class': 'cta-button'},
                                            'components': [{'type': 'textnode', 'content': 'Jetzt starten'}]
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            'tagName': 'section',
                            'attributes': {'class': 'features-section', 'data-section': 'features'},
                            'components': [
                                {
                                    'tagName': 'div',
                                    'attributes': {'class': 'container'},
                                    'components': [
                                        {
                                            'tagName': 'h2',
                                            'components': [{'type': 'textnode', 'content': 'Unsere Features'}]
                                        },
                                        {
                                            'tagName': 'div',
                                            'attributes': {'class': 'features-grid'},
                                            'components': [
                                                {
                                                    'tagName': 'div',
                                                    'attributes': {'class': 'feature-card'},
                                                    'components': [
                                                        {'tagName': 'h3', 'components': [{'type': 'textnode', 'content': 'Feature 1'}]},
                                                        {'tagName': 'p', 'components': [{'type': 'textnode', 'content': 'Beschreibung'}]}
                                                    ]
                                                },
                                                {
                                                    'tagName': 'div',
                                                    'attributes': {'class': 'feature-card'},
                                                    'components': [
                                                        {'tagName': 'h3', 'components': [{'type': 'textnode', 'content': 'Feature 2'}]},
                                                        {'tagName': 'p', 'components': [{'type': 'textnode', 'content': 'Beschreibung'}]}
                                                    ]
                                                },
                                                {
                                                    'tagName': 'div',
                                                    'attributes': {'class': 'feature-card'},
                                                    'components': [
                                                        {'tagName': 'h3', 'components': [{'type': 'textnode', 'content': 'Feature 3'}]},
                                                        {'tagName': 'p', 'components': [{'type': 'textnode', 'content': 'Beschreibung'}]}
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                'css': '''
                    .hero-section {
                        padding: 80px 20px;
                        text-align: center;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }
                    .hero-title {
                        font-size: 3rem;
                        margin-bottom: 20px;
                        font-weight: 700;
                    }
                    .hero-subtitle {
                        font-size: 1.5rem;
                        margin-bottom: 30px;
                    }
                    .cta-button {
                        padding: 15px 40px;
                        font-size: 1.2rem;
                        background: white;
                        color: #667eea;
                        border: none;
                        border-radius: 50px;
                        cursor: pointer;
                        font-weight: 600;
                    }
                    .features-section {
                        padding: 80px 20px;
                    }
                    .features-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 30px;
                        margin-top: 40px;
                    }
                    .feature-card {
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        background: white;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                    }
                ''',
                'layout_config': {
                    'sections': ['hero', 'features', 'testimonials', 'cta'],
                    'customizable': True,
                    'flexible_grid': True
                }
            },
            
            # Contact Page Template
            {
                'name': 'Kontaktseite',
                'slug': 'kontaktseite',
                'category': 'contact',
                'description': 'Flexibles Kontaktformular mit Kontaktinformationen und Karte',
                'html_json': {
                    'components': [
                        {
                            'tagName': 'section',
                            'attributes': {'class': 'contact-header', 'data-section': 'header'},
                            'components': [
                                {
                                    'tagName': 'div',
                                    'attributes': {'class': 'container'},
                                    'components': [
                                        {'tagName': 'h1', 'components': [{'type': 'textnode', 'content': 'Kontaktieren Sie uns'}]},
                                        {'tagName': 'p', 'components': [{'type': 'textnode', 'content': 'Wir freuen uns auf Ihre Nachricht'}]}
                                    ]
                                }
                            ]
                        },
                        {
                            'tagName': 'section',
                            'attributes': {'class': 'contact-content', 'data-section': 'content'},
                            'components': [
                                {
                                    'tagName': 'div',
                                    'attributes': {'class': 'container contact-grid'},
                                    'components': [
                                        {
                                            'tagName': 'div',
                                            'attributes': {'class': 'contact-form-wrapper'},
                                            'components': [
                                                {
                                                    'tagName': 'form',
                                                    'attributes': {'class': 'contact-form'},
                                                    'components': [
                                                        {
                                                            'tagName': 'div',
                                                            'attributes': {'class': 'form-group'},
                                                            'components': [
                                                                {'tagName': 'label', 'components': [{'type': 'textnode', 'content': 'Name'}]},
                                                                {'tagName': 'input', 'attributes': {'type': 'text', 'name': 'name', 'required': ''}}
                                                            ]
                                                        },
                                                        {
                                                            'tagName': 'div',
                                                            'attributes': {'class': 'form-group'},
                                                            'components': [
                                                                {'tagName': 'label', 'components': [{'type': 'textnode', 'content': 'E-Mail'}]},
                                                                {'tagName': 'input', 'attributes': {'type': 'email', 'name': 'email', 'required': ''}}
                                                            ]
                                                        },
                                                        {
                                                            'tagName': 'div',
                                                            'attributes': {'class': 'form-group'},
                                                            'components': [
                                                                {'tagName': 'label', 'components': [{'type': 'textnode', 'content': 'Nachricht'}]},
                                                                {'tagName': 'textarea', 'attributes': {'name': 'message', 'rows': '5', 'required': ''}}
                                                            ]
                                                        },
                                                        {
                                                            'tagName': 'button',
                                                            'attributes': {'type': 'submit', 'class': 'submit-button'},
                                                            'components': [{'type': 'textnode', 'content': 'Nachricht senden'}]
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            'tagName': 'div',
                                            'attributes': {'class': 'contact-info'},
                                            'components': [
                                                {'tagName': 'h3', 'components': [{'type': 'textnode', 'content': 'Kontaktinformationen'}]},
                                                {'tagName': 'p', 'components': [{'type': 'textnode', 'content': '📧 info@example.com'}]},
                                                {'tagName': 'p', 'components': [{'type': 'textnode', 'content': '📞 +49 123 456789'}]},
                                                {'tagName': 'p', 'components': [{'type': 'textnode', 'content': '📍 Musterstraße 1, 12345 Stadt'}]}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                'css': '''
                    .contact-header {
                        padding: 60px 20px;
                        text-align: center;
                        background: #f8f9fa;
                    }
                    .contact-content {
                        padding: 60px 20px;
                    }
                    .contact-grid {
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 40px;
                    }
                    .contact-form {
                        display: flex;
                        flex-direction: column;
                        gap: 20px;
                    }
                    .form-group {
                        display: flex;
                        flex-direction: column;
                    }
                    .form-group label {
                        margin-bottom: 8px;
                        font-weight: 600;
                    }
                    .form-group input,
                    .form-group textarea {
                        padding: 12px;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                        font-size: 1rem;
                    }
                    .submit-button {
                        padding: 15px 30px;
                        background: #667eea;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 1.1rem;
                        font-weight: 600;
                    }
                    .contact-info {
                        background: #f8f9fa;
                        padding: 30px;
                        border-radius: 10px;
                    }
                    .contact-info h3 {
                        margin-bottom: 20px;
                    }
                    .contact-info p {
                        margin: 10px 0;
                        font-size: 1.1rem;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                    }
                    @media (max-width: 768px) {
                        .contact-grid {
                            grid-template-columns: 1fr;
                        }
                    }
                ''',
                'layout_config': {
                    'sections': ['header', 'form', 'info', 'map'],
                    'form_integration': True,
                    'customizable': True
                }
            },
            
            # Sales Page Template
            {
                'name': 'Verkaufsseite',
                'slug': 'verkaufsseite',
                'category': 'sales',
                'description': 'Überzeugende Verkaufsseite mit Produktvorteilen und CTAs',
                'html_json': {
                    'components': [
                        {
                            'tagName': 'section',
                            'attributes': {'class': 'sales-hero', 'data-section': 'hero'},
                            'components': [
                                {
                                    'tagName': 'div',
                                    'attributes': {'class': 'container'},
                                    'components': [
                                        {'tagName': 'h1', 'components': [{'type': 'textnode', 'content': 'Das perfekte Produkt für Sie'}]},
                                        {'tagName': 'p', 'attributes': {'class': 'lead'}, 'components': [{'type': 'textnode', 'content': 'Lösen Sie Ihr Problem mit unserer Lösung'}]},
                                        {'tagName': 'button', 'attributes': {'class': 'cta-primary'}, 'components': [{'type': 'textnode', 'content': 'Jetzt kaufen'}]}
                                    ]
                                }
                            ]
                        },
                        {
                            'tagName': 'section',
                            'attributes': {'class': 'benefits-section', 'data-section': 'benefits'},
                            'components': [
                                {
                                    'tagName': 'div',
                                    'attributes': {'class': 'container'},
                                    'components': [
                                        {'tagName': 'h2', 'components': [{'type': 'textnode', 'content': 'Ihre Vorteile'}]},
                                        {
                                            'tagName': 'div',
                                            'attributes': {'class': 'benefits-grid'},
                                            'components': [
                                                {
                                                    'tagName': 'div',
                                                    'attributes': {'class': 'benefit-item'},
                                                    'components': [
                                                        {'tagName': 'div', 'attributes': {'class': 'benefit-icon'}, 'components': [{'type': 'textnode', 'content': '✓'}]},
                                                        {'tagName': 'h3', 'components': [{'type': 'textnode', 'content': 'Vorteil 1'}]},
                                                        {'tagName': 'p', 'components': [{'type': 'textnode', 'content': 'Beschreibung des Vorteils'}]}
                                                    ]
                                                },
                                                {
                                                    'tagName': 'div',
                                                    'attributes': {'class': 'benefit-item'},
                                                    'components': [
                                                        {'tagName': 'div', 'attributes': {'class': 'benefit-icon'}, 'components': [{'type': 'textnode', 'content': '✓'}]},
                                                        {'tagName': 'h3', 'components': [{'type': 'textnode', 'content': 'Vorteil 2'}]},
                                                        {'tagName': 'p', 'components': [{'type': 'textnode', 'content': 'Beschreibung des Vorteils'}]}
                                                    ]
                                                },
                                                {
                                                    'tagName': 'div',
                                                    'attributes': {'class': 'benefit-item'},
                                                    'components': [
                                                        {'tagName': 'div', 'attributes': {'class': 'benefit-icon'}, 'components': [{'type': 'textnode', 'content': '✓'}]},
                                                        {'tagName': 'h3', 'components': [{'type': 'textnode', 'content': 'Vorteil 3'}]},
                                                        {'tagName': 'p', 'components': [{'type': 'textnode', 'content': 'Beschreibung des Vorteils'}]}
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            'tagName': 'section',
                            'attributes': {'class': 'pricing-section', 'data-section': 'pricing'},
                            'components': [
                                {
                                    'tagName': 'div',
                                    'attributes': {'class': 'container'},
                                    'components': [
                                        {'tagName': 'h2', 'components': [{'type': 'textnode', 'content': 'Pricing'}]},
                                        {
                                            'tagName': 'div',
                                            'attributes': {'class': 'pricing-box'},
                                            'components': [
                                                {'tagName': 'div', 'attributes': {'class': 'price'}, 'components': [{'type': 'textnode', 'content': '99€'}]},
                                                {'tagName': 'p', 'components': [{'type': 'textnode', 'content': 'Einmalzahlung'}]},
                                                {'tagName': 'button', 'attributes': {'class': 'cta-primary'}, 'components': [{'type': 'textnode', 'content': 'Jetzt bestellen'}]}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                'css': '''
                    .sales-hero {
                        padding: 100px 20px;
                        text-align: center;
                        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                        color: white;
                    }
                    .sales-hero h1 {
                        font-size: 3rem;
                        margin-bottom: 20px;
                    }
                    .lead {
                        font-size: 1.5rem;
                        margin-bottom: 30px;
                    }
                    .cta-primary {
                        padding: 18px 50px;
                        font-size: 1.3rem;
                        background: white;
                        color: #f5576c;
                        border: none;
                        border-radius: 50px;
                        cursor: pointer;
                        font-weight: 700;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    }
                    .benefits-section {
                        padding: 80px 20px;
                        background: #f8f9fa;
                    }
                    .benefits-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                        gap: 30px;
                        margin-top: 40px;
                    }
                    .benefit-item {
                        text-align: center;
                        padding: 30px;
                        background: white;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    .benefit-icon {
                        font-size: 3rem;
                        color: #f5576c;
                        margin-bottom: 15px;
                    }
                    .pricing-section {
                        padding: 80px 20px;
                        text-align: center;
                    }
                    .pricing-box {
                        max-width: 400px;
                        margin: 40px auto;
                        padding: 40px;
                        background: white;
                        border-radius: 15px;
                        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    }
                    .price {
                        font-size: 4rem;
                        font-weight: 700;
                        color: #f5576c;
                        margin-bottom: 10px;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                    }
                ''',
                'layout_config': {
                    'sections': ['hero', 'benefits', 'testimonials', 'pricing', 'faq', 'cta'],
                    'conversion_optimized': True,
                    'customizable': True
                }
            },
            
            # Info Page Template
            {
                'name': 'Infoseite',
                'slug': 'infoseite',
                'category': 'info',
                'description': 'Flexible Infoseite für Inhalte, Dokumentation und Anleitungen',
                'html_json': {
                    'components': [
                        {
                            'tagName': 'section',
                            'attributes': {'class': 'info-header', 'data-section': 'header'},
                            'components': [
                                {
                                    'tagName': 'div',
                                    'attributes': {'class': 'container'},
                                    'components': [
                                        {'tagName': 'h1', 'components': [{'type': 'textnode', 'content': 'Informationen'}]},
                                        {'tagName': 'p', 'components': [{'type': 'textnode', 'content': 'Alles, was Sie wissen müssen'}]}
                                    ]
                                }
                            ]
                        },
                        {
                            'tagName': 'section',
                            'attributes': {'class': 'info-content', 'data-section': 'content'},
                            'components': [
                                {
                                    'tagName': 'div',
                                    'attributes': {'class': 'container content-layout'},
                                    'components': [
                                        {
                                            'tagName': 'aside',
                                            'attributes': {'class': 'sidebar'},
                                            'components': [
                                                {'tagName': 'h3', 'components': [{'type': 'textnode', 'content': 'Navigation'}]},
                                                {
                                                    'tagName': 'ul',
                                                    'attributes': {'class': 'nav-list'},
                                                    'components': [
                                                        {'tagName': 'li', 'components': [{'tagName': 'a', 'attributes': {'href': '#'}, 'components': [{'type': 'textnode', 'content': 'Abschnitt 1'}]}]},
                                                        {'tagName': 'li', 'components': [{'tagName': 'a', 'attributes': {'href': '#'}, 'components': [{'type': 'textnode', 'content': 'Abschnitt 2'}]}]},
                                                        {'tagName': 'li', 'components': [{'tagName': 'a', 'attributes': {'href': '#'}, 'components': [{'type': 'textnode', 'content': 'Abschnitt 3'}]}]}
                                                    ]
                                                }
                                            ]
                                        },
                                        {
                                            'tagName': 'article',
                                            'attributes': {'class': 'main-content'},
                                            'components': [
                                                {'tagName': 'h2', 'components': [{'type': 'textnode', 'content': 'Hauptinhalt'}]},
                                                {'tagName': 'p', 'components': [{'type': 'textnode', 'content': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'}]},
                                                {'tagName': 'h3', 'components': [{'type': 'textnode', 'content': 'Unterabschnitt'}]},
                                                {'tagName': 'p', 'components': [{'type': 'textnode', 'content': 'Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.'}]},
                                                {
                                                    'tagName': 'ul',
                                                    'components': [
                                                        {'tagName': 'li', 'components': [{'type': 'textnode', 'content': 'Punkt 1'}]},
                                                        {'tagName': 'li', 'components': [{'type': 'textnode', 'content': 'Punkt 2'}]},
                                                        {'tagName': 'li', 'components': [{'type': 'textnode', 'content': 'Punkt 3'}]}
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                'css': '''
                    .info-header {
                        padding: 60px 20px;
                        text-align: center;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }
                    .info-header h1 {
                        font-size: 2.5rem;
                        margin-bottom: 10px;
                    }
                    .info-content {
                        padding: 60px 20px;
                    }
                    .content-layout {
                        display: grid;
                        grid-template-columns: 250px 1fr;
                        gap: 40px;
                    }
                    .sidebar {
                        background: #f8f9fa;
                        padding: 20px;
                        border-radius: 10px;
                        height: fit-content;
                        position: sticky;
                        top: 20px;
                    }
                    .nav-list {
                        list-style: none;
                        padding: 0;
                    }
                    .nav-list li {
                        margin: 10px 0;
                    }
                    .nav-list a {
                        color: #667eea;
                        text-decoration: none;
                        font-weight: 500;
                    }
                    .main-content {
                        line-height: 1.8;
                    }
                    .main-content h2 {
                        font-size: 2rem;
                        margin-bottom: 20px;
                        color: #333;
                    }
                    .main-content h3 {
                        font-size: 1.5rem;
                        margin: 30px 0 15px;
                        color: #555;
                    }
                    .main-content p {
                        margin-bottom: 20px;
                        color: #666;
                    }
                    .main-content ul {
                        margin: 20px 0;
                        padding-left: 20px;
                    }
                    .main-content li {
                        margin: 10px 0;
                        color: #666;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                    }
                    @media (max-width: 768px) {
                        .content-layout {
                            grid-template-columns: 1fr;
                        }
                        .sidebar {
                            position: static;
                        }
                    }
                ''',
                'layout_config': {
                    'sections': ['header', 'sidebar', 'content', 'related'],
                    'documentation_friendly': True,
                    'customizable': True
                }
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates:
            template, created = PageTemplate.objects.update_or_create(
                slug=template_data['slug'],
                defaults={
                    'name': template_data['name'],
                    'category': template_data['category'],
                    'description': template_data['description'],
                    'html_json': template_data['html_json'],
                    'css': template_data['css'],
                    'layout_config': template_data['layout_config'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created template: {template.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⟳ Updated template: {template.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Done! Created {created_count} templates, updated {updated_count} templates'
            )
        )

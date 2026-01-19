"""Domain service for handling STRATO and custom domain configuration"""
import secrets
import dns.resolver
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from django.utils import timezone
from django.conf import settings
from ..models import LandingPage, DomainConfiguration


class DomainServiceError(Exception):
    """Custom exception for domain service errors"""
    pass


class StratoDomainService:
    """Service for handling STRATO domain configuration and DNS verification"""
    
    def __init__(self, landing_page: LandingPage):
        self.landing_page = landing_page
        # Get or create domain configuration
        self.domain_config, _ = DomainConfiguration.objects.get_or_create(
            landing_page=landing_page
        )
    
    def generate_verification_token(self) -> str:
        """
        Generate a unique verification token for DNS TXT record
        
        Returns:
            64-character hexadecimal token
        """
        token = secrets.token_hex(32)
        self.landing_page.dns_verification_token = token
        self.landing_page.save()
        return token
    
    def get_dns_instructions(self) -> Dict:
        """
        Generate STRATO-specific DNS setup instructions
        
        Returns:
            Dict with DNS records and step-by-step instructions
        """
        full_domain = self.landing_page.get_full_domain()
        
        if not full_domain:
            raise DomainServiceError("No domain configured for this landing page")
        
        # Generate verification token if not exists
        if not self.landing_page.dns_verification_token:
            self.generate_verification_token()
        
        # Get server IP (from settings or default)
        server_ip = getattr(settings, 'SERVER_IP', '0.0.0.0')
        
        # Determine DNS record type based on hosting type
        instructions = {
            'domain': full_domain,
            'hosting_type': self.landing_page.hosting_type,
            'verification_token': self.landing_page.dns_verification_token,
            'records': [],
            'strato_steps': []
        }
        
        if self.landing_page.hosting_type == 'strato' and self.landing_page.strato_subdomain:
            # Subdomain: Use CNAME record
            cname_target = getattr(settings, 'CNAME_TARGET', 'landing.example.com')
            
            instructions['records'].append({
                'type': 'CNAME',
                'name': self.landing_page.strato_subdomain,
                'value': cname_target,
                'ttl': 3600
            })
            
            # Update domain config
            self.domain_config.required_cname = cname_target
            
            instructions['strato_steps'] = [
                "1. Melden Sie sich im STRATO Kunden-Login an",
                "2. Navigieren Sie zu 'Domains' → Ihre Domain auswählen",
                "3. Klicken Sie auf 'DNS-Einstellungen'",
                f"4. Erstellen Sie einen neuen CNAME-Record:",
                f"   - Name/Host: {self.landing_page.strato_subdomain}",
                f"   - Typ: CNAME",
                f"   - Wert/Ziel: {cname_target}",
                "   - TTL: 3600 (oder Standard)",
                "5. Speichern Sie die Änderungen",
                "6. Warten Sie 5-15 Minuten auf DNS-Propagation"
            ]
        
        elif self.landing_page.hosting_type in ['custom', 'strato']:
            # Custom domain or main domain: Use A record
            instructions['records'].append({
                'type': 'A',
                'name': '@' if self.landing_page.hosting_type == 'strato' else full_domain,
                'value': server_ip,
                'ttl': 3600
            })
            
            # Update domain config
            self.domain_config.required_a_record = server_ip
            
            instructions['strato_steps'] = [
                "1. Melden Sie sich im STRATO Kunden-Login an",
                "2. Navigieren Sie zu 'Domains' → Ihre Domain auswählen",
                "3. Klicken Sie auf 'DNS-Einstellungen'",
                "4. Erstellen Sie einen neuen A-Record:",
                f"   - Name/Host: @ (für Hauptdomain) oder {full_domain}",
                "   - Typ: A",
                f"   - Wert/IP: {server_ip}",
                "   - TTL: 3600 (oder Standard)",
                "5. Speichern Sie die Änderungen",
                "6. Warten Sie 5-15 Minuten auf DNS-Propagation"
            ]
        
        # Add TXT record for verification
        txt_record_name = f"_telis-verify.{full_domain}" if '.' in full_domain else f"_telis-verify"
        instructions['records'].append({
            'type': 'TXT',
            'name': txt_record_name,
            'value': f"telis-verification={self.landing_page.dns_verification_token}",
            'ttl': 3600
        })
        
        # Update domain config
        self.domain_config.required_txt_record = f"telis-verification={self.landing_page.dns_verification_token}"
        self.domain_config.save()
        
        instructions['strato_steps'].extend([
            "",
            "Zusätzlich: TXT-Record für Verifizierung:",
            f"7. Erstellen Sie einen weiteren TXT-Record:",
            f"   - Name/Host: {txt_record_name}",
            "   - Typ: TXT",
            f"   - Wert: telis-verification={self.landing_page.dns_verification_token}",
            "   - TTL: 3600 (oder Standard)",
            "8. Speichern Sie die Änderungen"
        ])
        
        return instructions
    
    def verify_dns_configuration(self) -> Dict:
        """
        Verify DNS configuration using DNS lookups
        
        Returns:
            Dict with verification results
        """
        full_domain = self.landing_page.get_full_domain()
        
        if not full_domain:
            raise DomainServiceError("No domain configured for this landing page")
        
        results = {
            'domain': full_domain,
            'verified': False,
            'checks': {},
            'errors': [],
            'timestamp': timezone.now().isoformat()
        }
        
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 5
        
        # Check A or CNAME record
        try:
            if self.landing_page.hosting_type == 'strato' and self.landing_page.strato_subdomain:
                # Check CNAME for subdomain
                answers = resolver.resolve(full_domain, 'CNAME')
                cname_value = str(answers[0].target).rstrip('.')
                
                expected_cname = self.domain_config.required_cname
                results['checks']['cname'] = {
                    'found': cname_value,
                    'expected': expected_cname,
                    'match': cname_value == expected_cname
                }
                
                if cname_value != expected_cname:
                    results['errors'].append(f"CNAME record mismatch: found '{cname_value}', expected '{expected_cname}'")
            
            else:
                # Check A record for main domain
                answers = resolver.resolve(full_domain, 'A')
                a_value = str(answers[0])
                
                expected_ip = str(self.domain_config.required_a_record)
                results['checks']['a_record'] = {
                    'found': a_value,
                    'expected': expected_ip,
                    'match': a_value == expected_ip
                }
                
                if a_value != expected_ip:
                    results['errors'].append(f"A record mismatch: found '{a_value}', expected '{expected_ip}'")
        
        except dns.resolver.NXDOMAIN:
            results['errors'].append(f"Domain '{full_domain}' does not exist")
            results['checks']['domain_exists'] = False
        except dns.resolver.NoAnswer:
            results['errors'].append(f"No DNS records found for '{full_domain}'")
            results['checks']['records_found'] = False
        except Exception as e:
            results['errors'].append(f"DNS lookup error: {str(e)}")
        
        # Check TXT verification record
        txt_domain = f"_telis-verify.{full_domain}"
        try:
            answers = resolver.resolve(txt_domain, 'TXT')
            txt_values = [str(rdata).strip('"') for rdata in answers]
            
            expected_txt = self.domain_config.required_txt_record
            found_verification = any(expected_txt in txt for txt in txt_values)
            
            results['checks']['txt_verification'] = {
                'found': txt_values,
                'expected': expected_txt,
                'match': found_verification
            }
            
            if not found_verification:
                results['errors'].append(f"TXT verification record not found or incorrect")
        
        except dns.resolver.NXDOMAIN:
            results['errors'].append(f"TXT record domain '{txt_domain}' does not exist")
            results['checks']['txt_verification'] = {'found': None, 'match': False}
        except dns.resolver.NoAnswer:
            results['errors'].append(f"No TXT records found for '{txt_domain}'")
            results['checks']['txt_verification'] = {'found': None, 'match': False}
        except Exception as e:
            results['errors'].append(f"TXT lookup error: {str(e)}")
        
        # Determine if all checks passed
        all_checks = results['checks']
        
        if self.landing_page.hosting_type == 'strato' and self.landing_page.strato_subdomain:
            results['verified'] = (
                all_checks.get('cname', {}).get('match', False) and
                all_checks.get('txt_verification', {}).get('match', False)
            )
        else:
            results['verified'] = (
                all_checks.get('a_record', {}).get('match', False) and
                all_checks.get('txt_verification', {}).get('match', False)
            )
        
        # Update landing page
        self.landing_page.dns_verified = results['verified']
        self.landing_page.save()
        
        # Update domain config
        self.domain_config.last_dns_check = timezone.now()
        self.domain_config.dns_check_result = results
        self.domain_config.save()
        
        return results
    
    def get_nginx_config(self) -> str:
        """
        Generate nginx server block configuration
        
        Returns:
            nginx configuration as string
        """
        full_domain = self.landing_page.get_full_domain()
        
        if not full_domain:
            raise DomainServiceError("No domain configured for this landing page")
        
        ssl_enabled = self.landing_page.ssl_enabled
        protocol = 'https' if ssl_enabled else 'http'
        
        config = f"""# nginx configuration for {full_domain}
# Landing Page: {self.landing_page.title} ({self.landing_page.slug})

server {{
    listen 80;
    server_name {full_domain};
"""
        
        if ssl_enabled:
            config += f"""
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {full_domain};
    
    # SSL certificates (configure with certbot or your SSL provider)
    ssl_certificate /etc/ssl/certs/{full_domain}.crt;
    ssl_certificate_key /etc/ssl/private/{full_domain}.key;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
"""
        
        # Determine location
        if self.landing_page.is_uploaded_site:
            # Serve uploaded files directly
            config += f"""
    # Serve uploaded static site
    root {self.landing_page.uploaded_files_path};
    index {self.landing_page.entry_point};
    
    location / {{
        try_files $uri $uri/ /{self.landing_page.entry_point};
    }}
"""
        else:
            # Proxy to Django app
            config += """
    # Proxy to Django application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files
    location /static/ {
        alias /path/to/static/;
    }
    
    location /media/ {
        alias /path/to/media/;
    }
"""
        
        config += """
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Logging
    access_log /var/log/nginx/{domain}_access.log;
    error_log /var/log/nginx/{domain}_error.log;
}}
""".replace('{domain}', full_domain)
        
        return config

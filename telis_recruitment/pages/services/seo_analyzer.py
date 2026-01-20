"""SEO Analysis Service for Landing Pages"""
import re
from typing import Dict, List, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse


class SEOAnalyzer:
    """Analyzes landing pages for SEO best practices"""
    
    def __init__(self, page):
        """
        Initialize with a LandingPage instance
        
        Args:
            page: LandingPage model instance
        """
        self.page = page
        self.issues = []
        self.warnings = []
        self.suggestions = []
        self.score = 100
        
    def analyze(self) -> Dict[str, Any]:
        """
        Perform complete SEO analysis
        
        Returns:
            Dictionary with analysis results, score, and recommendations
        """
        self._check_title()
        self._check_description()
        self._check_headings()
        self._check_images()
        self._check_links()
        self._check_keywords()
        self._check_open_graph()
        self._check_url_slug()
        self._check_content_length()
        
        return {
            'score': max(0, self.score),
            'grade': self._get_grade(),
            'issues': self.issues,
            'warnings': self.warnings,
            'suggestions': self.suggestions,
            'details': {
                'title': self._get_title_details(),
                'description': self._get_description_details(),
                'headings': self._get_headings_details(),
                'images': self._get_images_details(),
                'links': self._get_links_details(),
            }
        }
    
    def _check_title(self):
        """Check SEO title"""
        title = self.page.seo_title or self.page.title
        
        if not title:
            self.issues.append("Missing SEO title")
            self.score -= 15
        elif len(title) < 30:
            self.warnings.append("SEO title is too short (< 30 characters)")
            self.score -= 5
        elif len(title) > 60:
            self.warnings.append("SEO title is too long (> 60 characters, may be truncated in search results)")
            self.score -= 5
        else:
            self.suggestions.append("SEO title length is optimal (30-60 characters)")
    
    def _check_description(self):
        """Check meta description"""
        description = self.page.seo_description
        
        if not description:
            self.issues.append("Missing meta description")
            self.score -= 15
        elif len(description) < 120:
            self.warnings.append("Meta description is too short (< 120 characters)")
            self.score -= 5
        elif len(description) > 160:
            self.warnings.append("Meta description is too long (> 160 characters, may be truncated)")
            self.score -= 5
        else:
            self.suggestions.append("Meta description length is optimal (120-160 characters)")
    
    def _check_headings(self):
        """Check heading structure in HTML"""
        if not self.page.html:
            return
        
        soup = BeautifulSoup(self.page.html, 'html.parser')
        
        h1_tags = soup.find_all('h1')
        if len(h1_tags) == 0:
            self.issues.append("No H1 heading found")
            self.score -= 10
        elif len(h1_tags) > 1:
            self.warnings.append(f"Multiple H1 headings found ({len(h1_tags)}). Should have only one.")
            self.score -= 5
        
        h2_tags = soup.find_all('h2')
        if len(h2_tags) == 0:
            self.suggestions.append("Consider adding H2 headings for better content structure")
    
    def _check_images(self):
        """Check images for alt text"""
        if not self.page.html:
            return
        
        soup = BeautifulSoup(self.page.html, 'html.parser')
        images = soup.find_all('img')
        
        images_without_alt = [img for img in images if not img.get('alt')]
        
        if images_without_alt:
            count = len(images_without_alt)
            self.warnings.append(f"{count} image(s) missing alt text")
            self.score -= min(count * 2, 10)
    
    def _check_links(self):
        """Check internal and external links"""
        if not self.page.html:
            return
        
        soup = BeautifulSoup(self.page.html, 'html.parser')
        links = soup.find_all('a')
        
        external_links = 0
        internal_links = 0
        broken_links = 0
        
        for link in links:
            href = link.get('href', '')
            if not href or href.startswith('#'):
                continue
            
            if href.startswith('http'):
                external_links += 1
                # External links should have rel="noopener" for security
                if not link.get('rel'):
                    broken_links += 1
            else:
                internal_links += 1
        
        if external_links > 0 and broken_links > 0:
            self.suggestions.append(f"{broken_links} external link(s) missing rel=\"noopener\" attribute")
    
    def _check_keywords(self):
        """Check if keywords are set"""
        if not self.page.seo_keywords:
            self.suggestions.append("Consider adding SEO keywords for better targeting")
    
    def _check_open_graph(self):
        """Check Open Graph tags"""
        og_title = self.page.og_title or self.page.seo_title
        og_description = self.page.og_description or self.page.seo_description
        og_image = self.page.og_image or self.page.seo_image
        
        if not og_title:
            self.warnings.append("Missing Open Graph title")
            self.score -= 3
        
        if not og_description:
            self.warnings.append("Missing Open Graph description")
            self.score -= 3
        
        if not og_image:
            self.warnings.append("Missing Open Graph image")
            self.score -= 4
    
    def _check_url_slug(self):
        """Check URL slug"""
        slug = self.page.slug
        
        if len(slug) > 50:
            self.suggestions.append("URL slug is quite long. Consider using a shorter, more concise slug.")
        
        if '_' in slug:
            self.suggestions.append("URL slug contains underscores. Hyphens are preferred for SEO.")
        
        # Check for numbers at the start
        if slug and slug[0].isdigit():
            self.suggestions.append("URL slug starts with a number. Consider starting with a keyword.")
    
    def _check_content_length(self):
        """Check content length"""
        if not self.page.html:
            return
        
        soup = BeautifulSoup(self.page.html, 'html.parser')
        text = soup.get_text()
        word_count = len(text.split())
        
        if word_count < 300:
            self.warnings.append(f"Content is short ({word_count} words). Aim for at least 300 words for better SEO.")
            self.score -= 5
        elif word_count > 2000:
            self.suggestions.append(f"Content is quite long ({word_count} words). Consider breaking into multiple pages.")
    
    def _get_grade(self) -> str:
        """Get letter grade based on score"""
        if self.score >= 90:
            return 'A'
        elif self.score >= 80:
            return 'B'
        elif self.score >= 70:
            return 'C'
        elif self.score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _get_title_details(self) -> Dict[str, Any]:
        """Get title analysis details"""
        title = self.page.seo_title or self.page.title or ''
        return {
            'text': title,
            'length': len(title),
            'optimal': 30 <= len(title) <= 60,
        }
    
    def _get_description_details(self) -> Dict[str, Any]:
        """Get description analysis details"""
        description = self.page.seo_description or ''
        return {
            'text': description,
            'length': len(description),
            'optimal': 120 <= len(description) <= 160,
        }
    
    def _get_headings_details(self) -> Dict[str, Any]:
        """Get headings analysis details"""
        if not self.page.html:
            return {'h1_count': 0, 'h2_count': 0, 'h3_count': 0}
        
        soup = BeautifulSoup(self.page.html, 'html.parser')
        return {
            'h1_count': len(soup.find_all('h1')),
            'h2_count': len(soup.find_all('h2')),
            'h3_count': len(soup.find_all('h3')),
        }
    
    def _get_images_details(self) -> Dict[str, Any]:
        """Get images analysis details"""
        if not self.page.html:
            return {'total': 0, 'with_alt': 0, 'without_alt': 0}
        
        soup = BeautifulSoup(self.page.html, 'html.parser')
        images = soup.find_all('img')
        with_alt = len([img for img in images if img.get('alt')])
        
        return {
            'total': len(images),
            'with_alt': with_alt,
            'without_alt': len(images) - with_alt,
        }
    
    def _get_links_details(self) -> Dict[str, Any]:
        """Get links analysis details"""
        if not self.page.html:
            return {'total': 0, 'internal': 0, 'external': 0}
        
        soup = BeautifulSoup(self.page.html, 'html.parser')
        links = soup.find_all('a')
        
        external = len([l for l in links if l.get('href', '').startswith('http')])
        
        return {
            'total': len(links),
            'external': external,
            'internal': len(links) - external,
        }

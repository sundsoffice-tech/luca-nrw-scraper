/* ============================================
   LUCA Lead Finder - Interactive JavaScript
   ============================================ */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
    initScrollProgress();
    initMobileMenu();
    initSmoothScroll();
    initScrollReveal();
    initCounters();
    initTypingEffect();
    initMagneticButtons();
    initNewsletterForm();
    initNavbarScroll();
});

/* ============================================
   Scroll Progress Bar
   ============================================ */
function initScrollProgress() {
    const progressBar = document.getElementById('scroll-progress');
    
    window.addEventListener('scroll', () => {
        const windowHeight = window.innerHeight;
        const documentHeight = document.documentElement.scrollHeight;
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollPercent = (scrollTop / (documentHeight - windowHeight)) * 100;
        
        progressBar.style.width = `${scrollPercent}%`;
    });
}

/* ============================================
   Mobile Menu Toggle
   ============================================ */
function initMobileMenu() {
    const menuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (menuBtn && mobileMenu) {
        menuBtn.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
            
            // Change icon
            const icon = menuBtn.querySelector('i');
            if (mobileMenu.classList.contains('hidden')) {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            } else {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            }
        });
        
        // Close menu when clicking on a link
        const mobileLinks = mobileMenu.querySelectorAll('a');
        mobileLinks.forEach(link => {
            link.addEventListener('click', () => {
                mobileMenu.classList.add('hidden');
                const icon = menuBtn.querySelector('i');
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            });
        });
    }
}

/* ============================================
   Smooth Scroll for Navigation
   ============================================ */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            
            if (target) {
                const offsetTop = target.offsetTop - 80; // Account for fixed nav
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/* ============================================
   Scroll Reveal Animation
   ============================================ */
function initScrollReveal() {
    const revealElements = document.querySelectorAll('.reveal-on-scroll');
    
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    revealElements.forEach(element => {
        revealObserver.observe(element);
    });
}

/* ============================================
   Animated Counter
   ============================================ */
function initCounters() {
    const counters = document.querySelectorAll('.counter');
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px'
    };
    
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.classList.contains('counted')) {
                const target = parseInt(entry.target.getAttribute('data-target'));
                animateCounter(entry.target, target);
                entry.target.classList.add('counted');
            }
        });
    }, observerOptions);
    
    counters.forEach(counter => {
        counterObserver.observe(counter);
    });
}

function animateCounter(element, target) {
    const duration = 2000; // 2 seconds
    const steps = 60;
    const increment = target / steps;
    let current = 0;
    const stepDuration = duration / steps;
    
    const timer = setInterval(() => {
        current += increment;
        
        if (current >= target) {
            element.textContent = target.toLocaleString('de-DE');
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current).toLocaleString('de-DE');
        }
    }, stepDuration);
}

/* ============================================
   Typing Effect for Hero
   ============================================ */
function initTypingEffect() {
    const typingElement = document.getElementById('typing-text');
    if (!typingElement) return;
    
    const words = [
        'Vertriebsprofis',
        'Unternehmen',
        'Recruiter',
        'Sales Teams'
    ];
    
    let wordIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    
    function type() {
        const currentWord = words[wordIndex];
        
        if (isDeleting) {
            typingElement.textContent = currentWord.substring(0, charIndex - 1);
            charIndex--;
        } else {
            typingElement.textContent = currentWord.substring(0, charIndex + 1);
            charIndex++;
        }
        
        let typeSpeed = isDeleting ? 50 : 100;
        
        if (!isDeleting && charIndex === currentWord.length) {
            typeSpeed = 2000; // Pause at end
            isDeleting = true;
        } else if (isDeleting && charIndex === 0) {
            isDeleting = false;
            wordIndex = (wordIndex + 1) % words.length;
            typeSpeed = 500; // Pause before next word
        }
        
        setTimeout(type, typeSpeed);
    }
    
    // Start typing effect
    setTimeout(type, 1000);
}

/* ============================================
   Magnetic Buttons Effect
   ============================================ */
function initMagneticButtons() {
    const magneticButtons = document.querySelectorAll('.magnetic-btn');
    
    magneticButtons.forEach(button => {
        button.addEventListener('mousemove', (e) => {
            const rect = button.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            
            button.style.transform = `translate(${x * 0.15}px, ${y * 0.15}px)`;
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translate(0, 0)';
        });
    });
}

/* ============================================
   Newsletter Form Submission
   ============================================ */
function initNewsletterForm() {
    const form = document.getElementById('newsletter-form');
    const successMessage = document.getElementById('success-message');
    const emailInput = document.getElementById('email-input');
    
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const email = emailInput.value;
            
            // Show loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Senden...';
            submitBtn.disabled = true;
            
            // Simulate API call (replace with actual API endpoint)
            await new Promise(resolve => setTimeout(resolve, 1500));
            
            // Show success message
            successMessage.classList.remove('hidden');
            emailInput.value = '';
            
            // Reset button
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
            
            // Hide success message after 5 seconds
            setTimeout(() => {
                successMessage.classList.add('hidden');
            }, 5000);
            
            // Log for demo purposes (remove in production)
            console.log('Newsletter signup:', email);
        });
    }
}

/* ============================================
   Navbar Scroll Effect
   ============================================ */
function initNavbarScroll() {
    const nav = document.querySelector('nav');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
    });
}

/* ============================================
   Parallax Effect (Optional Enhancement)
   ============================================ */
function initParallax() {
    const shapes = document.querySelectorAll('.shape');
    
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        
        shapes.forEach((shape, index) => {
            const speed = 0.5 + (index * 0.1);
            const yPos = -(scrolled * speed);
            shape.style.transform = `translateY(${yPos}px)`;
        });
    });
}

// Optional: Initialize parallax
// Uncomment the line below to enable parallax effect
// initParallax();

/* ============================================
   Easter Egg: Konami Code
   ============================================ */
let konamiCode = [];
const konamiPattern = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];

document.addEventListener('keydown', (e) => {
    konamiCode.push(e.key);
    konamiCode = konamiCode.slice(-10);
    
    if (konamiCode.join(',') === konamiPattern.join(',')) {
        activateEasterEgg();
    }
});

function activateEasterEgg() {
    // Add fun animation or effect
    document.body.style.animation = 'rainbow 2s linear';
    
    // Show a fun message
    const message = document.createElement('div');
    message.textContent = '🚀 Super LUCA Mode aktiviert! 🚀';
    message.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #22d3ee, #8b5cf6);
        padding: 20px 40px;
        border-radius: 12px;
        font-size: 24px;
        font-weight: bold;
        z-index: 10000;
        animation: slideDown 0.5s ease;
    `;
    
    document.body.appendChild(message);
    
    setTimeout(() => {
        message.remove();
    }, 3000);
}

/* ============================================
   Performance Monitoring (Optional)
   ============================================ */
function logPerformance() {
    if ('performance' in window) {
        window.addEventListener('load', () => {
            const perfData = performance.timing;
            const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
            console.log(`Page Load Time: ${pageLoadTime}ms`);
        });
    }
}

// Enable performance monitoring in development
// logPerformance();

/* ============================================
   Utility Functions
   ============================================ */

// Debounce function for scroll events
function debounce(func, wait = 10) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle function for frequently fired events
function throttle(func, limit = 100) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Check if element is in viewport
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/* ============================================
   Console Message (Branding)
   ============================================ */
console.log(
    '%c🚀 LUCA Lead Finder',
    'font-size: 20px; font-weight: bold; color: #22d3ee; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);'
);
console.log(
    '%cInterested in how this works? Check out the code!',
    'font-size: 14px; color: #8b5cf6;'
);
console.log(
    '%c💼 Karriere bei LUCA? careers@luca-leadfinder.de',
    'font-size: 12px; color: #6366f1;'
);

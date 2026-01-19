# Changelog

All notable changes to LUCA NRW Scraper will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Release process and versioning system
- Configuration profiles (production, high-volume, debug)
- Security checklist for production deployments
- Support bundle system for diagnostics
- Standardized error reporting in UI

## [2.4.0] - 2026-01-19

### Added
- **Security enhancements**: SSL/TLS validation enabled by default
- **Security**: Secure defaults for production (ALLOW_INSECURE_SSL=0 by default)
- **Security**: Security warnings when insecure mode is activated
- **Configuration**: Extended scraper configuration model with SSL settings
- **Documentation**: Comprehensive security implementation guide

### Changed
- Default SSL validation from insecure (1) to secure (0)
- SSL warnings now only suppressed when explicitly enabled
- Improved security documentation in .env.example

### Security
- ⚠️ **BREAKING CHANGE**: SSL certificate validation is now enabled by default
- Users with self-signed certificates must explicitly set `ALLOW_INSECURE_SSL=1`

## [2.3.0] - Previous Release

### Added
- Django CRM dashboard with KPIs and lead management
- Landing page builder with GrapesJS visual editor
- Brevo email marketing integration
- Mailbox system for email management
- Multi-portal scraper support
- Role-based access control (Admin/Manager/Telefonist)
- Advanced lead filtering and export capabilities
- AI-powered lead validation and scoring
- Talent Hunt mode for finding active sales professionals
- Parallel crawling for improved performance

### Features
- Real-time scraper monitoring and control
- CSV/Excel export with custom filters
- REST API for integrations
- Mobile-responsive design
- Automated lead deduplication
- Industry-specific query optimization

### Infrastructure
- Docker support for easy deployment
- WhiteNoise for static file serving
- PostgreSQL and SQLite support
- Production-ready settings with environment variables

---

## Release Types

- **Major (X.0.0)**: Breaking changes, major feature additions, architecture changes
- **Minor (x.X.0)**: New features, enhancements, non-breaking changes
- **Patch (x.x.X)**: Bug fixes, security patches, minor improvements

## Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements or vulnerability fixes

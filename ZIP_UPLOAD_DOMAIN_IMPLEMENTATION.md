# ZIP/File Upload and STRATO Domain-Hosting Implementation

## Overview

This implementation adds two major features to the TELIS CRM pages app:

1. **ZIP/File Upload System** - Upload complete websites as ZIP files or manage individual files
2. **STRATO Domain Integration** - Configure custom domains with STRATO DNS hosting

## Features Implemented

### 1. ZIP/File Upload System

#### Models
- Extended `LandingPage` with upload-related fields:
  - `is_uploaded_site` - Flag for uploaded websites
  - `uploaded_files_path` - Path to uploaded files directory
  - `entry_point` - Main entry file (e.g., index.html)

- New `UploadedFile` model:
  - Tracks individual uploaded files
  - Stores file metadata (size, type, path)
  - Unique constraint on landing_page + relative_path

#### Upload Service (`services/upload_service.py`)
- **ZIP Upload Processing:**
  - Validates ZIP size (max 100MB)
  - Validates file count (max 500 files)
  - ZIP bomb protection (3x compression ratio limit)
  - Auto-detects root directory in ZIP
  - Auto-detects entry point (index.html, etc.)
  - Creates database records for all files

- **Single File Upload:**
  - Validates file type (whitelist of allowed extensions)
  - Validates file size (max 10MB per file)
  - Path sanitization (prevents directory traversal)
  - Creates/updates file records

- **File Management:**
  - Delete individual files
  - Generate file tree structure
  - List all uploaded files

#### Security Features
- **Allowed File Types:** .html, .htm, .css, .js, .json, .png, .jpg, .jpeg, .gif, .svg, .webp, .ico, .woff, .woff2, .ttf, .eot, .otf, .pdf, .txt, .xml, .webmanifest, .mp4, .webm, .mp3, .wav
- **Path Sanitization:** Prevents directory traversal attacks
- **Size Limits:** 100MB for ZIP, 10MB for single files
- **ZIP Bomb Protection:** Checks uncompressed size ratio

#### Upload Manager UI (`templates/pages/upload_manager.html`)
- Drag & drop zone for ZIP files
- Drag & drop zone for single files
- Real-time upload progress
- File browser with tree view
- Entry point configuration
- File deletion
- Statistics display (file count, total size)
- Dark theme consistent with CRM

### 2. STRATO Domain Integration

#### Models
- Extended `LandingPage` with domain fields:
  - `hosting_type` - Internal, STRATO, or Custom
  - `custom_domain` - Custom domain name
  - `strato_subdomain` - STRATO subdomain
  - `strato_main_domain` - STRATO main domain
  - `ssl_enabled` - SSL/HTTPS toggle
  - `dns_verified` - DNS verification status
  - `dns_verification_token` - Unique verification token

- New `DomainConfiguration` model:
  - STRATO customer ID and API key (encrypted)
  - Required DNS records (A, CNAME, TXT)
  - Last DNS check timestamp
  - DNS check results (JSON)

#### Domain Service (`services/domain_service.py`)
- **DNS Verification:**
  - Generates unique verification tokens
  - Creates STRATO-specific DNS instructions
  - Verifies DNS configuration using dns.resolver
  - Checks A/CNAME records
  - Checks TXT verification records
  - Updates verification status

- **nginx Configuration:**
  - Generates server block configuration
  - SSL/HTTPS support
  - Proxy or static file serving
  - Security headers

#### Domain Settings UI (`templates/pages/domain_settings.html`)
- Hosting type selection (Internal/STRATO/Custom)
- Domain configuration forms
- STRATO DNS setup instructions
- DNS verification status
- Real-time DNS verification
- nginx configuration download
- Dark theme consistent with CRM

### 3. API Endpoints

#### Upload Management (Staff Only)
- `GET /pages/upload/{slug}/` - Upload manager interface
- `POST /pages/api/{slug}/upload/zip/` - Upload ZIP file
- `POST /pages/api/{slug}/upload/file/` - Upload single file
- `POST /pages/api/{slug}/upload/delete/` - Delete file
- `GET /pages/api/{slug}/upload/list/` - List files (JSON)
- `GET /pages/api/{slug}/upload/stats/` - Get statistics (JSON)
- `POST /pages/api/{slug}/upload/entry-point/` - Set entry point

#### Domain Management (Staff Only)
- `GET /pages/domain/{slug}/` - Domain settings interface
- `POST /pages/api/{slug}/domain/save/` - Save domain settings
- `POST /pages/api/{slug}/domain/verify/` - Verify DNS configuration
- `GET /pages/api/{slug}/domain/nginx/` - Download nginx config

#### Public
- `GET /p/{slug}/static/{file_path}` - Serve uploaded static files

### 4. Admin Interface Updates

#### LandingPage Admin
- Added "Upload Manager" and "Domain Settings" links
- New "Hosting" badge showing hosting type and status
- New fieldsets for Upload and Domain settings
- Enhanced list display with hosting and verification status

#### New Admin Interfaces
- **UploadedFile Admin:**
  - List view with file details
  - Read-only interface
  - Human-readable file sizes
  - Filter by landing page, file type, date

- **DomainConfiguration Admin:**
  - DNS status display
  - STRATO configuration fields
  - DNS check results viewer
  - Read-only interface

## Database Migrations

Migration `0003_landingpage_custom_domain_and_more.py` adds:
- 10 new fields to LandingPage
- UploadedFile model
- DomainConfiguration model

## Dependencies

Added to `requirements.txt`:
- `dnspython>=2.4.0` - For DNS verification

## Security Considerations

1. **Upload Security:**
   - Whitelist-based file type validation
   - File size limits enforced
   - Path sanitization prevents directory traversal
   - ZIP bomb protection
   - Staff-only access to upload endpoints

2. **Domain Security:**
   - DNS verification required before activation
   - Encrypted storage for API keys
   - CSRF protection on all POST endpoints
   - Staff-only access to domain endpoints

3. **File Serving:**
   - Only published pages can serve files
   - File path validation
   - Content-type detection
   - Proper file handle cleanup

## Testing

All existing tests pass:
- 10 tests in pages app
- No security vulnerabilities detected by CodeQL
- Code review completed and issues addressed

## Usage Instructions

### Uploading a Website

1. Navigate to Landing Pages in admin
2. Click "Upload Manager" for the desired page
3. Drag & drop a ZIP file or use "Choose File" button
4. Files are automatically extracted and tracked
5. Entry point is auto-detected (or set manually)
6. View files in the file browser

### Configuring a Domain

1. Navigate to Landing Pages in admin
2. Click "Domain Settings" for the desired page
3. Select hosting type (Internal/STRATO/Custom)
4. Enter domain details
5. Save settings to generate DNS instructions
6. Follow STRATO-specific setup steps
7. Click "DNS Verify" to check configuration
8. Download nginx config for server setup

### Serving Uploaded Sites

Once a site is uploaded and the page is published:
- Main page: `/p/{slug}/`
- Static files: `/p/{slug}/static/{file_path}`
- Custom domain: Configure via Domain Settings

## File Structure

```
telis_recruitment/pages/
├── models.py                    # Extended models
├── views.py                     # Existing builder views
├── views_upload.py              # New upload/domain views
├── urls.py                      # Updated URL config
├── public_urls.py               # Updated public URLs
├── admin.py                     # Enhanced admin interface
├── services/
│   ├── __init__.py
│   ├── upload_service.py        # Upload handling
│   └── domain_service.py        # DNS/domain handling
├── templates/pages/
│   ├── builder.html             # Existing builder
│   ├── builder_list.html        # Existing list
│   ├── public_page.html         # Existing public page
│   ├── upload_manager.html      # New upload UI
│   └── domain_settings.html     # New domain UI
└── migrations/
    └── 0003_landingpage_custom_domain_and_more.py
```

## Future Enhancements

Possible improvements for future iterations:

1. **Upload System:**
   - WebP image optimization
   - Automatic responsive image generation
   - Version control for uploaded sites
   - Diff viewer for file changes
   - Bulk file operations

2. **Domain System:**
   - Automatic SSL certificate provisioning (Let's Encrypt)
   - CDN integration
   - Multiple domain aliases
   - Automatic DNS configuration via STRATO API
   - Domain transfer wizard

3. **General:**
   - Preview uploaded sites before publishing
   - A/B testing between builder and uploaded versions
   - Analytics integration
   - SEO analysis for uploaded sites
   - Automated backups

## Support

For issues or questions:
1. Check the admin interface for error messages
2. Review logs for detailed error information
3. Verify DNS configuration with the verification tool
4. Ensure file types and sizes are within limits
5. Contact support for STRATO-specific DNS issues

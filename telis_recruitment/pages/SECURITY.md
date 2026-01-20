# Page Builder Security Documentation

## Overview

The Page Builder allows staff members to upload complete HTML/CSS/JavaScript projects as ZIP files. While this provides powerful flexibility, it also introduces security considerations that all users should understand.

## Security Model

### Access Control
- **All upload functionality is restricted to staff members only** (`@staff_member_required` decorator)
- Public users cannot access upload interfaces
- Only authenticated Django admin users can upload projects

### File Type Restrictions
The upload service enforces a whitelist of allowed file extensions:
- **Web Files**: `.html`, `.htm`, `.css`, `.js`, `.json`
- **Images**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.webp`, `.ico`
- **Fonts**: `.woff`, `.woff2`, `.ttf`, `.eot`, `.otf`
- **Media**: `.mp4`, `.webm`, `.mp3`, `.wav`
- **Documents**: `.pdf`, `.txt`, `.xml`, `.webmanifest`

### Path Traversal Protection
- All file paths are sanitized to prevent directory traversal attacks
- `..` sequences and absolute paths are blocked
- Hidden files (starting with `.`) are skipped during ZIP extraction

## JavaScript Upload Risks

### ⚠️ Important Security Notice

**JavaScript files (`.js`) are allowed in uploads** to support modern web development. However, this means:

1. **Arbitrary Code Execution**: Uploaded JavaScript runs in the visitor's browser when they view published pages
2. **XSS Potential**: Malicious JavaScript could steal user data or session tokens
3. **Trust Required**: Only upload projects from **trusted sources**

### Risk Mitigation

The following security measures are in place:

1. **Staff-Only Access**: Only authenticated staff members can upload projects
2. **Sandboxed Rendering**: Uploaded pages are served with security headers
3. **Content Security Policy**: CSP headers limit what uploaded JavaScript can do
4. **Same-Origin Policy**: Uploaded pages run in a separate context

## Content Security Policy (CSP)

Uploaded pages are served with the following CSP headers to limit potential damage:

```
Content-Security-Policy: 
    default-src 'self';
    script-src 'self' 'unsafe-inline' 'unsafe-eval';
    style-src 'self' 'unsafe-inline';
    img-src 'self' data: https:;
    font-src 'self' data:;
    connect-src 'self';
    frame-ancestors 'none';
```

**Important Notes:**
- `'unsafe-inline'` and `'unsafe-eval'` are enabled to support most HTML/JS projects
- This reduces some CSP protections but is necessary for functionality
- Always review uploaded content before publishing

## Best Practices

### For Staff Members

1. **Review Before Publishing**
   - Inspect JavaScript files in uploaded ZIP archives
   - Test pages in draft mode before publishing
   - Look for suspicious code patterns (obfuscated code, eval() calls, etc.)

2. **Trust Your Sources**
   - Only upload projects you created yourself or from trusted sources
   - Be extra cautious with projects from external developers
   - Scan files with antivirus before uploading

3. **Monitor Published Pages**
   - Regularly review published pages for unauthorized changes
   - Check analytics for unusual visitor behavior
   - Monitor for security reports from visitors

4. **Use Draft Mode**
   - Always upload new projects as drafts first
   - Test thoroughly before changing status to published
   - Verify all functionality works as expected

### For Administrators

1. **User Training**
   - Ensure all staff members understand the risks
   - Provide training on identifying malicious code
   - Establish a review process for external projects

2. **Audit Logs**
   - Monitor who uploads projects and when
   - Review the upload history regularly
   - Investigate suspicious upload patterns

3. **Backup Strategy**
   - Maintain backups of all uploaded projects
   - Have a rollback plan in case of security incidents
   - Test restoration procedures regularly

## Recommended Workflow

```
1. Receive HTML/JS Project
   ↓
2. Review Code Locally
   - Scan for malicious patterns
   - Verify all JavaScript functionality
   ↓
3. Upload as Draft
   - Use Page Builder upload interface
   - Keep status as "draft"
   ↓
4. Test Thoroughly
   - Check all pages and functionality
   - Verify no security issues
   ↓
5. Publish
   - Change status to "published"
   - Monitor visitor activity
```

## Security Incident Response

If you discover a security issue in an uploaded project:

1. **Immediately unpublish** the affected page(s)
2. **Document** what was found and when
3. **Review** upload history to identify the source
4. **Notify** system administrators
5. **Investigate** if any visitor data was compromised
6. **Update** security procedures if needed

## Technical Details

### Upload Processing Flow

```python
1. ZIP file uploaded by staff member
2. Validate file size (max 100MB)
3. Check for ZIP bomb (max 3x expansion)
4. Extract to temporary directory
5. Validate each file:
   - Check extension against whitelist
   - Skip hidden files
   - Prevent path traversal
   - Check individual file size
6. Copy validated files to permanent location
7. Create database records
8. Clean up temporary files
```

### File Serving

Uploaded files are served with:
- Proper Content-Type headers
- Content-Security-Policy headers
- X-Frame-Options: DENY (prevents embedding in iframes from other domains)
- X-Content-Type-Options: nosniff

## Additional Resources

- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [Content Security Policy Guide](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)

## Questions?

If you have questions about page builder security, contact your system administrator.

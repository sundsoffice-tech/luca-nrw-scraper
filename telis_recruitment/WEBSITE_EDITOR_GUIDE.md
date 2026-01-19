# Website Editor Documentation

## Overview

The Website Editor is a comprehensive code editing solution built on top of Monaco Editor (the same editor that powers VS Code). It extends the existing Landing Page Builder system to support full website development with file management, version control, and live preview.

## Features

### 🎨 Monaco Editor Integration
- Professional code editor with syntax highlighting
- Support for 20+ file types: HTML, CSS, JavaScript, JSON, Markdown, TypeScript, Python, PHP, etc.
- IntelliSense and autocompletion
- Minimap navigation
- Line numbers and code folding
- Dark theme matching the TELIS CRM

### 📁 File Management
- **File Tree Navigation**: Visual folder structure in left panel
- **Multi-File Tabs**: Edit multiple files simultaneously
- **Context Menu**: Right-click for quick actions
- **File Operations**:
  - Create new files
  - Rename files
  - Move files to different folders
  - Duplicate files
  - Delete files
- **Folder Operations**:
  - Create new folders
  - Delete folders (recursive)

### 🔍 Search & Navigation
- **Content Search**: Search across all files by name or content
- **Quick Open**: Press Ctrl+P for quick file access
- **File Preview**: Click any file in tree to open

### 💾 Version Control
- **Automatic Versioning**: Versions created on each save
- **Version History**: View all previous versions of a file
- **Restore**: Roll back to any previous version
- **Version Notes**: Add notes to describe changes

### 👁️ Live Preview
- **Split View**: Preview panel alongside editor
- **Hot Reload**: Preview updates automatically on save
- **Device Simulation**: Test responsive designs (planned)
- **Full Screen**: Toggle preview panel as needed

### 📦 Project Templates
- **Starter Templates**: Blank HTML, Bootstrap, Tailwind CSS
- **Custom Templates**: Save projects as reusable templates
- **Template Import**: Apply templates to new projects
- **Template Export**: Export entire project as ZIP

### ⚡ Keyboard Shortcuts
- `Ctrl+S` / `Cmd+S` - Save current file
- `Ctrl+P` / `Cmd+P` - Quick open / Search
- Tab management with click and close

## Architecture

### Backend Components

#### Models (`models.py`)
```python
FileVersion       # Version history for files
ProjectTemplate   # Reusable project templates
```

#### Services
```python
EditorService     # File operations and content management
VersionService    # Version control and history tracking
TemplateService   # Template management and application
UploadService     # File upload and ZIP handling (existing)
```

#### Views (`views_editor.py`)
All editor endpoints are prefixed with `/crm/pages/editor/<slug>/`:
- `GET /editor/<slug>/` - Main editor interface
- `GET /api/<slug>/editor/file/` - Get file content
- `POST /api/<slug>/editor/file/save/` - Save file content
- `POST /api/<slug>/editor/file/create/` - Create new file
- `POST /api/<slug>/editor/file/rename/` - Rename file
- `POST /api/<slug>/editor/file/move/` - Move file
- `POST /api/<slug>/editor/file/duplicate/` - Duplicate file
- `POST /api/<slug>/editor/folder/create/` - Create folder
- `POST /api/<slug>/editor/folder/delete/` - Delete folder
- `GET /api/<slug>/editor/search/` - Search files
- `GET /api/<slug>/editor/versions/` - Get version history
- `POST /api/<slug>/editor/restore/` - Restore version
- `GET /api/<slug>/export/` - Export as ZIP
- `POST /api/<slug>/import/` - Import template

### Frontend Components

#### Main Template (`website_editor.html`)
```
┌─────────────────────────────────────────────────┐
│ Header: Page Info, Actions                      │
├──────────┬────────────────────────┬──────────────┤
│ File     │ Editor Tabs            │ Preview      │
│ Tree     ├────────────────────────┤ (Optional)   │
│          │ Monaco Editor          │              │
│          │                        │              │
│          ├────────────────────────┤              │
│          │ Status Bar             │              │
└──────────┴────────────────────────┴──────────────┘
```

#### JavaScript State Management
```javascript
state = {
    currentFile: null,          // Currently open file path
    openTabs: [],              // Array of open file paths
    activeTab: null,           // Currently active tab
    editor: null,              // Monaco editor instance
    fileTree: null,            // File tree structure
    unsavedChanges: {},        // Track unsaved files
    contextTarget: null,       // Right-click target
    modalCallback: null        // Current modal callback
}
```

## Usage Guide

### Accessing the Editor

1. Navigate to **Landing Pages** in the CRM
2. For uploaded websites, click **💻 Editor**
3. Or use the direct URL: `/crm/pages/editor/<page-slug>/`

### Working with Files

#### Opening Files
- Click any file in the file tree
- Files open in new tabs
- Multiple files can be open simultaneously

#### Creating Files
1. Click the 📄 button in the toolbar, OR
2. Right-click in the file tree → Create File
3. Enter the file path (e.g., `css/style.css`)
4. File is created and opened in editor

#### Editing Files
1. Type in the Monaco editor
2. Unsaved changes are marked with `•` in tab
3. Press `Ctrl+S` to save
4. Status bar shows save status

#### Renaming Files
1. Right-click file → Rename
2. Enter new path
3. All references update automatically

#### Deleting Files
1. Right-click file → Delete
2. Confirm deletion
3. File removed from disk and database

### Working with Folders

#### Creating Folders
1. Click 📁 button in toolbar, OR
2. Create a file with a path like `css/components/button.css`
3. Folders are created automatically

#### Deleting Folders
1. Right-click folder → Delete Folder
2. Confirm deletion
3. All files in folder are removed

### Version Control

#### Viewing History
1. Open a file
2. Click version icon (planned UI)
3. See list of all versions with timestamps and notes

#### Restoring Versions
1. Select a version from history
2. Click Restore
3. File content reverts to that version
4. New version is created with restored content

### Live Preview

#### Enabling Preview
1. Click **👁️ Preview** button
2. Preview panel appears on right
3. Shows the published page

#### Refreshing Preview
- Preview auto-refreshes on save
- Click 🔄 in preview panel to manually refresh
- Preview loads entry point (usually `index.html`)

### Templates

#### Using Templates
1. Create new landing page
2. Click Import Template
3. Select from available templates
4. Files are copied to your project

#### Creating Templates
1. Export your project as ZIP
2. Admin can create ProjectTemplate
3. Add to template gallery

### Searching

#### Search Files
1. Click 🔍 search button OR press `Ctrl+P`
2. Enter search term
3. Results show matching files and content context
4. Choose to search filenames only or content

## API Reference

### Get File Content
```http
GET /api/<slug>/editor/file/?path=<file-path>
```
Response:
```json
{
  "success": true,
  "data": {
    "content": "file content",
    "path": "index.html",
    "size": 1024,
    "type": "text/html",
    "language": "html",
    "editable": true
  }
}
```

### Save File Content
```http
POST /api/<slug>/editor/file/save/
Content-Type: application/json

{
  "path": "index.html",
  "content": "new content",
  "create_version": true,
  "version_note": "Updated header"
}
```

### Create File
```http
POST /api/<slug>/editor/file/create/
Content-Type: application/json

{
  "path": "css/new-style.css",
  "content": "/* styles */"
}
```

### Search Files
```http
GET /api/<slug>/editor/search/?query=button&search_content=true
```

Response:
```json
{
  "success": true,
  "query": "button",
  "count": 3,
  "results": [
    {
      "path": "css/style.css",
      "match_type": "content",
      "context": "...btn-primary { color: button...",
      "size": 2048,
      "type": "text/css"
    }
  ]
}
```

## Configuration

### Editable File Types
Defined in `EditorService.EDITABLE_EXTENSIONS`:
```python
EDITABLE_EXTENSIONS = {
    '.html', '.htm', '.css', '.js', '.json', '.txt', '.md',
    '.xml', '.svg', '.webmanifest', '.ts', '.jsx', '.tsx',
    '.py', '.php', '.rb', '.java', '.c', '.cpp', '.h',
    '.yaml', '.yml', '.toml', '.ini', '.conf', '.sh'
}
```

### Version Limits
- Maximum versions per file: 50 (configurable in `VersionService`)
- Older versions automatically cleaned up

### File Size Limits
- Single file: 10MB
- ZIP upload: 100MB
- Max files in ZIP: 500

## Security

### Authentication
- All editor endpoints require staff authentication
- Uses Django's `@staff_member_required` decorator

### Path Sanitization
- All file paths are sanitized
- Directory traversal attacks prevented
- Paths normalized before disk access

### Permissions
- Only staff users can access editor
- Version history tracks user who made changes
- All operations logged

## Troubleshooting

### Monaco Editor Not Loading
- Check browser console for errors
- Ensure CDN is accessible
- Verify Monaco loader script loaded

### Files Not Saving
- Check network tab for API errors
- Verify CSRF token is present
- Check file permissions on server

### Preview Not Updating
- Ensure page is published
- Check entry point is set correctly
- Manually refresh preview

### File Tree Not Showing
- Refresh with 🔄 button
- Check console for API errors
- Verify files exist in database

## Future Enhancements

### Planned Features
- [ ] Resizable panels with drag
- [ ] Device simulation (mobile/tablet/desktop)
- [ ] Git integration
- [ ] Collaborative editing
- [ ] Diff view between versions
- [ ] Terminal integration
- [ ] File upload via drag-and-drop to tree
- [ ] Bulk operations
- [ ] Undo/Redo across sessions
- [ ] Code snippets library
- [ ] AI-assisted coding

### Performance Optimizations
- [ ] Lazy load large files
- [ ] Virtual scrolling for file tree
- [ ] Debounced auto-save
- [ ] Service worker for offline editing
- [ ] WebSocket for real-time updates

## Integration with Existing Features

### Landing Page Builder
- Editor is complementary to GrapesJS builder
- Use GrapesJS for visual editing
- Use Monaco Editor for code-level control

### Upload Manager
- Bulk upload files via Upload Manager
- Edit individual files in Code Editor
- Both update same file database

### Domain Settings
- Configure custom domains
- Editor works with all hosting types
- Preview respects domain configuration

## Support

For issues or questions:
1. Check this documentation
2. Review error messages in browser console
3. Check Django logs for server errors
4. Contact system administrator

## Changelog

### Version 1.0.0 (2026-01-19)
- Initial release
- Monaco Editor integration
- File and folder operations
- Version control
- Live preview
- Template system
- Search functionality
- Multi-tab editing
- Context menus
- Keyboard shortcuts

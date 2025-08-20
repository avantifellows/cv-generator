# Resume Editing and Sharing Feature

This document describes the new UUID-based resume editing and sharing functionality added to the CV Generator.

## Overview

The CV Generator now supports:
- **Persistent Resume Storage**: Each resume gets a unique UUID and is saved locally
- **Auto-save**: Form data is automatically saved as you type
- **Resume Editing**: Return to edit your resume using the saved URL
- **Resume Sharing**: Share completed resumes with others in view-only mode
- **URL Management**: Easy copying of edit and share URLs

## How It Works

### 1. Creating a New Resume
- Visit the main URL (`/`)
- A new UUID is automatically generated
- You're redirected to `/resume/{uuid}` where you can fill out the form

### 2. Auto-save Functionality
- Form data is automatically saved every 2 seconds after you stop typing
- Draft data is saved locally in the `resume_data/` folder
- Each resume has a JSON file with the UUID as the filename

### 3. Returning to Edit
- Copy the current URL (e.g., `/resume/abc123-def456`)
- When you return to this URL, your previous data will be loaded
- You can continue editing from where you left off

### 4. Sharing Resumes
- Share your resume anytime (even if not completed) by clicking "Share URL"
- Use the share URL (e.g., `/resume/abc123-def456/view`)
- Others can view your resume but cannot edit it
- Draft resumes show a warning that they may be incomplete

## File Structure

```
resume_data/
├── resume_metadata.json          # Index of all resumes
├── abc123-def456.json           # Individual resume data
├── ghi789-jkl012.json           # Another resume
└── ...
```

## API Endpoints

### Resume Management
- `GET /` - Create new resume and redirect to UUID-based URL
- `GET /resume/{uuid}` - Edit resume (loads existing data if available)
- `GET /resume/{uuid}/view` - View-only mode for shared resumes (no edit form, works for drafts too)
- `POST /resume/{uuid}/save` - Save draft data (auto-save endpoint)
- `GET /resume/{uuid}/share` - Get shareable link (works for any resume status)

### Existing Endpoints
- `POST /generate` - Generate CV (now supports resume_id)
- `GET /cv/{cv_id}` - View generated CV
- `GET /cv/{cv_id}/pdf` - Download PDF

## Features

### Auto-save
- Saves every 2 seconds after user stops typing
- No notifications shown to avoid spam (automatic background saving)
- Saves on form submission

### URL Copy Popup
- Warns users before closing the tab if resume is not completed
- Shows message: "Please copy the URL to edit later your resume."
- Provides easy copy buttons for both edit and share URLs

### Resume Information Panel
- Shows current resume ID
- Displays edit URL with copy button (for returning to edit)
- Shows share URL with copy button (for sharing with others)
- Provides helpful tips and auto-save status

### View-only Mode
- Any resume (completed or draft) can be shared via `/resume/{uuid}/view`
- Shows banner indicating it's a shared resume
- No editing capabilities
- Clean, professional appearance
- Draft resumes show a warning about being incomplete

### Button Functionality
- **Copy Edit URL**: Copies the current URL for returning to edit later
- **Copy Share URL**: Saves current draft and copies the shareable link to clipboard
- **Auto-save**: Works silently in background every 2 seconds

## Technical Implementation

### Storage Service
- `ResumeStorageService` class handles all storage operations
- Supports local file storage (easily extensible to S3)
- Maintains metadata index for quick lookups
- Handles cleanup of old incomplete resumes

### Data Persistence
- Resume data is stored in structured JSON format
- Includes creation and modification timestamps
- Tracks completion status
- Compatible with existing CV data models

### Error Handling
- Graceful fallbacks if storage operations fail
- Logging for debugging and monitoring
- User-friendly error messages

## Future Enhancements

### S3 Integration
- The storage service is designed to easily switch to S3
- Factory pattern allows different storage backends
- Metadata structure remains consistent

### User Authentication
- Could add user accounts to manage multiple resumes
- Resume ownership and privacy controls
- Collaboration features

### Resume Templates
- Multiple CV templates/styles
- Template switching without losing data
- Custom styling options

## Usage Examples

### For Resume Creators
1. Visit the CV Generator
2. Fill out your resume information (auto-saves every 2 seconds)
3. Copy the Edit URL to return later
4. Click "Copy Share URL" to copy the shareable link
5. Share the copied URL with others for view-only access

### For Resume Viewers
1. Click on a shared resume link
2. View the resume in read-only mode
3. Download as PDF if needed
4. Create your own resume using the main generator

## Configuration

### Storage Type
- Currently set to "local" storage
- Can be changed to "s3" in the future
- Storage path is configurable

### Auto-save Timing
- Default: 2 seconds after user stops typing
- Configurable in the JavaScript code
- Can be adjusted based on user preferences

### Cleanup Settings
- Old incomplete resumes are cleaned up after 30 days
- Configurable cleanup interval
- Helps manage storage space

## Troubleshooting

### Resume Not Loading
- Check if the UUID is correct
- Verify the resume file exists in `resume_data/`
- Check application logs for errors

### Auto-save Not Working
- Ensure JavaScript is enabled
- Check browser console for errors
- Verify the resume_id is present

### Storage Issues
- Check disk space in the `resume_data/` folder
- Verify file permissions
- Check application logs for storage errors

## Security Considerations

### Data Privacy
- Resume data is stored locally by default
- No data is sent to external services
- Users control their own data

### URL Security
- UUIDs are randomly generated
- No sequential or predictable patterns
- URLs are not indexed by search engines

### Access Control
- Anyone with the URL can view/edit (if not completed)
- Consider adding authentication for production use
- Implement rate limiting for storage operations

# How the Download Button Works

## Overview

The "Download All as TXT" button (📥 Download All as TXT) exports all sidebar content from the application as a single text file, with each section separated by a special delimiter `###\n###`.

## Location in Code

The functionality is implemented in `index.html` starting at **line 2043**.

## Step-by-Step Process

### 1. **Button Click Handler** (line 2044-2045)

```javascript
downloadAllBtn.addEventListener('click', async () => {
    console.log('📥 Generating combined TXT file from IndexedDB...');
```

When clicked, the button triggers an async function that generates a combined export file.

### 2. **Access Templates Data** (line 2048-2052)

```javascript
if (typeof templates === 'undefined') {
    alert('❌ Templates not loaded yet. Please refresh the page.');
    return;
}
```

The function first checks if the `templates` object (from `script.js`) is loaded. This object contains all the sidebar items and their content.

### 3. **Get Current Database** (line 2054-2056)

```javascript
const databaseSelect = document.getElementById('databaseSelect');
const databaseName = databaseSelect ? databaseSelect.value :
    (window.DEFAULT_DATABASE_NAME || 'basketballStorage');
```

Retrieves the currently selected database name from the dropdown (e.g., "Basketball Storage", "Vocab Chinese", etc.).

### 4. **Define Delimiter** (line 2058-2060)

```javascript
const delimiter = '###\n###';
const sections = [];
```

Sets up the special delimiter that will separate each section in the exported file.

**Important**: This is the key separator pattern - three hashes, newline, three hashes.

### 5. **Sort Templates** (line 2062-2064)

```javascript
const sortedTemplates = Object.entries(templates)
    .sort((a, b) => a[1].title.localeCompare(b[1].title));
```

Sorts all sidebar items alphabetically by title for consistent export order.

### 6. **Process Each Sidebar Item** (line 2067-2102)

For each sidebar item, the function:

#### a. Extract Section Information (lines 2068-2072)
```javascript
const sectionTitle = template.title;
const keyName = sectionTitle.split('(')[0].trim().replace(/\s+/g, '_');
```

- Gets the section title (e.g., "basketball_handles (txt)")
- Generates a key name by removing file extension suffix: `"basketball_handles (txt)"` → `"basketball_handles"`

#### b. Convert HTML to Markdown (lines 2074-2075)
```javascript
const originalContent = htmlToMarkdown(template.content || '');
```

Uses the `htmlToMarkdown()` helper function (defined at line 2019) to convert any HTML links in the content to markdown format: `<a href="url">text</a>` → `[text](url)`.

#### c. Load User Notes from IndexedDB (lines 2077-2099)
```javascript
try {
    const snapshot = await window.indexedDBWrapper.get(databaseName, keyName);

    if (snapshot.exists()) {
        const textareaNotes = snapshot.val();

        if (textareaNotes && textareaNotes.trim()) {
            contentToExport = `${originalContent}\n\n--- Notes ---\n${textareaNotes}`;
        }
    }
} catch (error) {
    console.error(`Error loading ${keyName}:`, error);
}
```

- Attempts to load user-written notes from IndexedDB
- If notes exist, combines them with the original content using the separator `--- Notes ---`
- If no notes exist or there's an error, just uses the original content

#### d. Add to Sections Array (line 2101)
```javascript
sections.push(`${sectionTitle}\n${contentToExport}`);
```

Adds the formatted section (title + content) to the sections array.

### 7. **Combine All Sections** (line 2104-2105)

```javascript
const combinedContent = sections.join(`\n${delimiter}\n`);
```

Joins all sections together with the delimiter `###\n###` between each section.

**Example output structure:**
```
basketball_handles (txt)
Original content here...

--- Notes ---
User notes here...

###
###

drill_progressions (txt)
Original content here...

--- Notes ---
User notes here...

###
###

...
```

### 8. **Create and Download File** (lines 2107-2120)

```javascript
const blob = new Blob([combinedContent], { type: 'text/plain;charset=utf-8' });
const url = URL.createObjectURL(blob);
const link = document.createElement('a');
link.href = url;

const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
link.download = `${databaseName}_export_${timestamp}.txt`;

document.body.appendChild(link);
link.click();
document.body.removeChild(link);
URL.revokeObjectURL(url);
```

- Creates a text blob from the combined content
- Generates a filename with database name and timestamp: `basketballStorage_export_2025-10-18T14-30-45.txt`
- Triggers automatic download
- Cleans up the temporary URL

### 9. **Success Notification** (lines 2122-2123)

```javascript
console.log(`✅ Downloaded ${sortedTemplates.length} sections from "${databaseName}" to ${link.download}`);
showHeaderNotification(`✅ Exported ${sortedTemplates.length} sections from ${databaseName}`, 'success');
```

Shows console log and on-screen notification confirming the export.

## Key Features

1. **Delimiter-based separation**: Each section is separated by `###\n###` for easy parsing during import
2. **Database-specific export**: Only exports content from the currently selected database
3. **Notes preservation**: Combines original content with user-written notes (if any exist in IndexedDB)
4. **Alphabetical sorting**: Sections are sorted by title for consistent organization
5. **Timestamp in filename**: Each export has a unique filename with database name and timestamp
6. **Markdown conversion**: HTML links are automatically converted to markdown format

## Related Functions

- **Import Function**: The companion import function (starting at line 2178) reads files with this same delimiter format
- **htmlToMarkdown()**: Helper function (line 2019) that converts HTML links to markdown
- **IndexedDB wrapper**: Used to retrieve saved notes for each section

## File Format Specification

**Exported file structure:**
```
[Section Title]
[Original Content]

--- Notes ---
[User Notes from IndexedDB]

###
###

[Next Section Title]
[Original Content]

--- Notes ---
[User Notes from IndexedDB]

###
###

...
```

**Filename format:**
```
{databaseName}_export_{YYYY-MM-DDTHH-MM-SS}.txt
```

Example: `basketballStorage_export_2025-10-18T14-30-45.txt`

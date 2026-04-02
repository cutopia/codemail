# Example Codemail Format

## Subject Line Format

The subject line must follow this pattern:
```
codemail:[project-name]
```

Where:
- `codemail:` - Required prefix (case-insensitive)
- `[project-name]` - Project name in square brackets
- **No instructions** - Instructions are now in the email body only

## Examples of Valid Subject Lines

### Basic Example
```
Subject: codemail:[my-web-app]
```

### With Project Name Only
```
Subject: CODEMAIL:[api-service]
```

### Case Insensitive
```
Subject: Codemail: [data-pipeline]
```

## Examples of Invalid Subject Lines (Will Be Ignored)

### Missing Prefix
```
Subject: [my-project]  # ❌ Missing "codemail:" prefix
```

### Wrong Format
```
Subject: codemail my-project  # ❌ Missing brackets around project name
```

### Instructions in Subject (Not Allowed)
```
Subject: codemail:[project] Fix the bug  # ❌ Instructions should be in body only
```

## Email Body

The email body must contain detailed instructions for the AI agent. The subject line contains only the project name, while the body provides all task instructions.

### Basic Body
```
Fix the login button styling on the homepage.
The button should be blue with white text.
Make sure it works on mobile devices too.
```

### Structured Instructions
```
# Task: Fix login button

## Project: my-web-app

## Instructions:
1. Locate the login button in `src/components/Header.js`
2. Update the styling to use the new color scheme
3. Test on Chrome, Firefox, and Safari
4. Run unit tests before committing
```

## Complete Email Example

### Subject
```
codemail:[frontend-app]
```

### Body
```
Please implement a dark mode toggle feature for our frontend application.

Requirements:
1. Add a toggle button in the header component
2. Store user preference in localStorage
3. Apply dark theme class to body element when enabled
4. Use CSS variables for theme colors

Files to modify:
- src/components/Header.js
- src/styles/theme.css
- src/utils/storage.js

Test the feature in Chrome and Firefox before submitting.
```

## Configuration

You can customize the prefix by setting the `CODEMAIL_PREFIX` environment variable:

```bash
export CODEMAIL_PREFIX="task:"
```

With this configuration, valid subjects would be:
```
task:[project-name]
TASK:[Project-Name]
```

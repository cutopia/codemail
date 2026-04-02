# Example Codemail Format

## Subject Line Format

The subject line must follow this pattern:
```
codemail:[project-name] instructions
```

Where:
- `codemail:` - Required prefix (case-insensitive)
- `[project-name]` - Project name in square brackets
- `instructions` - The task or instructions for the AI agent

## Examples of Valid Subject Lines

### Basic Example
```
Subject: codemail:[my-web-app] Fix the login button styling
```

### Complex Instructions
```
Subject: codemail:[api-service] Add rate limiting to the user authentication endpoint
```

### With Additional Context in Body
```
Subject: codemail:[data-pipeline] Optimize the ETL process

Please optimize the data pipeline for better performance.
The main bottleneck is in the transformation stage.
Consider using batch processing instead of row-by-row processing.
```

## Examples of Invalid Subject Lines (Will Be Ignored)

### Missing Prefix
```
Subject: [my-project] Fix the bug  # ❌ Missing "codemail:" prefix
```

### Wrong Format
```
Subject: codemail my-project Fix the bug  # ❌ Missing brackets around project name
```

### No Project Name
```
Subject: codemail: Fix the bug  # ❌ Missing project name in brackets
```

## Email Body

The email body should contain detailed instructions for the AI agent. The subject line contains the project name and brief instructions, while the body can provide more context.

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
codemail:[frontend-app] Implement dark mode toggle
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
task:[project-name] instructions
TASK:[Project-Name] Instructions
```

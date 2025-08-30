# Transfer Issue to Markdown File

A powerful GitHub Action that automatically converts GitHub issues with specific labels into markdown files, perfect for static site generators and blog platforms. This action creates a pull request with the converted files for your review.

## 🚀 Features

- **Automatic Conversion**: Converts GitHub issues to markdown files with proper formatting
- **Label-based Filtering**: Only processes issues with both `blog` and `need_published` labels
- **Front Matter Support**: Adds YAML front matter with metadata for static site generators
- **Sanitized Filenames**: Ensures safe, valid filenames with date prefixes
- **Pull Request Creation**: Automatically creates a PR with converted files
- **Configurable Output**: Customize output directory and processing options
- **Type Hints**: Full type annotation for better code maintainability
- **Robust Error Handling**: Graceful error handling with detailed logging

## 📋 Requirements

- GitHub repository with issues
- Issues must have both `blog` and `need_published` labels to be processed
- GitHub token with repository access

## 🔧 Usage

### Basic Example

```yml
name: Convert Issues to Blog Posts
on:
  push:
    branches: [ main ]
  issues:
    types: [opened, edited, labeled]
  workflow_dispatch:

jobs:
  convert:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Convert Issues to Markdown
        uses: ONGOING-Z/transfer-issue-to-md-file@v2.0.0
        with:
          my-token: ${{ secrets.GITHUB_TOKEN }}
          path: "./blog/posts"
```

### Advanced Example with Schedule

```yml
name: Scheduled Blog Post Generation
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
  workflow_dispatch:

jobs:
  generate-posts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Generate Blog Posts from Issues
        uses: ONGOING-Z/transfer-issue-to-md-file@v2.0.0
        with:
          my-token: ${{ secrets.GITHUB_TOKEN }}
          path: "./content/posts"
```

## 📥 Action Inputs

| Name     | Description                                             | Required | Default    |
|----------|--------------------------------------------------------|----------|------------|
| my-token | GitHub token with repository access                    | Yes      | -          |
| path     | Directory to save the generated markdown files         | Yes      | `./issues` |

## 📤 Generated File Format

Each issue is converted to a markdown file with:

- **Filename**: `YYYY-MM-DD-issue-title.md`
- **Content**: Includes YAML front matter with metadata

### Example Output

```markdown
---
title: Your Issue Title
date: 2024-01-15 10:30:00
author: username
issue_number: 42
labels: blog, need_published, tutorial
---

Your issue content goes here...
```

## ⚙️ Configuration

You can customize the behavior by creating a `config.py` file in your repository:

```python
# Required labels for an issue to be published
REQUIRED_LABELS = {"blog", "need_published"}

# Date format for markdown file names
DATE_FORMAT = "%Y-%m-%d"

# Include front matter in markdown files
INCLUDE_FRONT_MATTER = True

# Process only open issues
ISSUE_STATE_FILTER = "open"

# Maximum number of issues to process
MAX_ISSUES_TO_PROCESS = None
```

## 🔄 Workflow

1. **Issue Creation**: Create an issue with your blog content
2. **Label Assignment**: Add `blog` and `need_published` labels
3. **Action Trigger**: Push to main branch or trigger manually
4. **Conversion**: Action converts matching issues to markdown
5. **Pull Request**: Creates PR with converted files
6. **Review & Merge**: Review the PR and merge when ready

## 🎯 Optimizations in v2.0.0

- **Performance**: Reduced API calls by filtering issues efficiently
- **Type Safety**: Added comprehensive type hints
- **Error Handling**: Improved error handling with detailed logging
- **Code Quality**: Refactored for better maintainability
- **Dependencies**: Updated to latest stable versions
- **Python Version**: Upgraded to Python 3.11 for better performance
- **GitHub Actions**: Updated deprecated syntax (`set-output` → `$GITHUB_OUTPUT`)

## 🐛 Troubleshooting

### No files generated?
- Ensure issues have both required labels: `blog` and `need_published`
- Check that issues are in the correct state (default: open)
- Verify GitHub token has proper permissions

### Pull request not created?
- Check if there are actual changes (new markdown files)
- Ensure the action has write permissions to create PRs

## 📝 License

[MIT][license_addr]

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🔗 Related Projects

- [peter-evans/create-pull-request][1] - Used for creating pull requests

[1]: https://github.com/peter-evans/create-pull-request
[license_addr]: https://github.com/ONGOING-Z/transfer-issue-to-md-file/blob/main/LICENSE

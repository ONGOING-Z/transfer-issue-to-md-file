# Transfer Issue to Markdown File

A Github action transfers issue with 'blog' and 'need_published' labels content to markdown file. After that, this action will create a pull
request to your current branch. And you can merge it manually.

In this action, I use this action - [create pull request][1] to make PR.

Note: only issues which have 'blog' and 'need_published' labels will be auto processed.

## Usage

example
```yml
name: CI
on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Transfer Issues to Markdown
        uses: ONGOING-Z/transfer-issue-to-md-file@v1.0.5
        with:
          my-token: ${{ secrets.MY_TOKEN }}
          path: "./blog-posts"
```

## Action inputs
| Name     | Description                                             | Default  |
|----------|---------------------------------------------------------|----------|
| my-token | the token that can access your repository               |          |
| path     | directory you want to save the generated markdown files | ./issues |

All inputs are **required**.

## Action Outputs
None

## Recent Optimizations (v1.0.5)

### 🚀 Performance Improvements
- **Faster API calls**: Now filters issues by 'blog' label at the API level, reducing data transfer
- **Better file handling**: Uses modern Python pathlib for more efficient path operations
- **Optimized processing**: Improved loop efficiency and reduced redundant operations

### 🛡️ Security & Reliability
- **Updated dependencies**: All packages updated to latest secure versions
- **Enhanced error handling**: Comprehensive error catching and graceful failure handling
- **Input validation**: Added parameter validation to prevent runtime errors

### 🔧 Code Quality
- **Type hints**: Added type annotations for better code maintainability
- **Modern Python**: Upgraded to Python 3.11 for better performance
- **Clean code**: Removed global variables and improved function naming
- **Better logging**: Enhanced logging with more informative messages

### 📝 Enhanced Output
- **Rich markdown**: Generated files now include frontmatter with metadata
- **Safe filenames**: Automatic sanitization of issue titles for valid filenames
- **UTF-8 encoding**: Proper encoding handling for international characters

## License

[MIT][license_addr]


[1]: https://github.com/peter-evans/create-pull-request
[license_addr]: https://github.com/ONGOING-Z/transfer-issue-to-md-file/blob/main/LICENSE

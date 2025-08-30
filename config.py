"""Configuration settings for the GitHub Issue to Markdown converter."""

# Required labels for an issue to be published
REQUIRED_LABELS = {"blog", "need_published"}

# Date format for markdown file names
DATE_FORMAT = "%Y-%m-%d"

# Maximum filename length (excluding date prefix and extension)
MAX_FILENAME_LENGTH = 200

# Default output directory if not specified
DEFAULT_OUTPUT_PATH = "./issues"

# Include front matter in markdown files
INCLUDE_FRONT_MATTER = True

# Process only open issues (set to None to process all)
ISSUE_STATE_FILTER = "open"

# Maximum number of issues to process (set to None for unlimited)
MAX_ISSUES_TO_PROCESS = None

# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = "INFO"
"""
Used for create blog by github repo issues.
"""
# -*- coding: utf-8 -*-

import os
import sys
import time
from pathlib import Path
from typing import List, Optional

from github import Github, GithubException, Issue
from github.Repository import Repository
from github.NamedUser import NamedUser
from loguru import logger

try:
    from config import (
        REQUIRED_LABELS,
        DATE_FORMAT,
        MAX_FILENAME_LENGTH,
        INCLUDE_FRONT_MATTER,
        ISSUE_STATE_FILTER,
        MAX_ISSUES_TO_PROCESS,
        LOG_LEVEL
    )
except ImportError:
    # Fallback to default values if config file doesn't exist
    REQUIRED_LABELS = {"blog", "need_published"}
    DATE_FORMAT = "%Y-%m-%d"
    MAX_FILENAME_LENGTH = 200
    INCLUDE_FRONT_MATTER = True
    ISSUE_STATE_FILTER = "open"
    MAX_ISSUES_TO_PROCESS = None
    LOG_LEVEL = "INFO"

# Configure logger
logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)


def get_github_client(token: str) -> Github:
    """Create and return a GitHub client.
    
    Args:
        token: GitHub access token
        
    Returns:
        Github client instance
        
    Raises:
        SystemExit: If token is invalid
    """
    try:
        client = Github(token)
        # Test the token by making a simple API call
        client.get_user().login
        logger.info("Successfully authenticated with GitHub")
        return client
    except GithubException as e:
        logger.error(f"Failed to authenticate with GitHub: {e}")
        sys.exit(1)


def get_repository(client: Github, repo_full_name: str) -> Repository:
    """Get repository by full name.
    
    Args:
        client: GitHub client
        repo_full_name: Repository full name (owner/repo)
        
    Returns:
        Repository object
        
    Raises:
        SystemExit: If repository not found
    """
    try:
        return client.get_repo(repo_full_name)
    except GithubException as e:
        logger.error(f"Failed to get repository {repo_full_name}: {e}")
        sys.exit(1)


def get_publishable_issues(repo: Repository) -> List[Issue.Issue]:
    """Get issues with required labels for publishing.
    
    Args:
        repo: Repository object
        
    Returns:
        List of issues to be published
    """
    publishable_issues = []
    total_issues = 0
    
    # Get issues based on configuration
    issues_iterator = repo.get_issues(state=ISSUE_STATE_FILTER) if ISSUE_STATE_FILTER else repo.get_issues()
    
    for issue in issues_iterator:
        total_issues += 1
        
        # Skip pull requests (they're included in issues API)
        if issue.pull_request:
            continue
        
        # Check if issue has required labels
        issue_labels = {label.name for label in issue.labels}
        if REQUIRED_LABELS.issubset(issue_labels):
            publishable_issues.append(issue)
    
    logger.info(
        f"Found {len(publishable_issues)} publishable issues out of {total_issues} open issues"
    )
    
    if publishable_issues:
        logger.debug(f"Issues to publish: {[issue.title for issue in publishable_issues]}")
    
    return publishable_issues


def process_issues(issues: List[Issue.Issue], output_path: str) -> int:
    """Process and save issues as markdown files.
    
    Args:
        issues: List of issues to process
        output_path: Directory to save markdown files
        
    Returns:
        Number of issues processed
    """
    processed_count = 0
    
    for issue in issues:
        try:
            write_issue_to_md_file(issue, output_path)
            processed_count += 1
            logger.info(f"Successfully processed issue: {issue.title}")
        except Exception as e:
            logger.error(f"Failed to process issue '{issue.title}': {e}")
            continue
    
    return processed_count





def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters for filenames
    invalid_chars = '<>:"|?*\n\r\t'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    
    # Replace forward/back slashes with hyphens
    filename = filename.replace('/', '-').replace('\\', '-')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit filename length (leave room for date prefix and .md extension)
    if len(filename) > MAX_FILENAME_LENGTH:
        filename = filename[:MAX_FILENAME_LENGTH]
    
    return filename or 'untitled'


def write_issue_to_md_file(issue: Issue.Issue, output_path: str) -> None:
    """Write issue content to markdown file.
    
    Args:
        issue: GitHub issue object
        output_path: Directory to save the file
        
    Raises:
        IOError: If file cannot be written
    """
    # Ensure output directory exists
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename with date prefix
    date_prefix = time.strftime(DATE_FORMAT, time.localtime())
    safe_title = sanitize_filename(issue.title)
    filename = f"{date_prefix}-{safe_title}.md"
    
    # Full file path
    file_path = output_dir / filename
    
    # Prepare content with metadata header
    content = prepare_markdown_content(issue)
    
    # Write file
    try:
        file_path.write_text(content, encoding='utf-8')
        logger.info(f"Issue '{issue.title}' saved to {file_path}")
    except IOError as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        raise


def prepare_markdown_content(issue: Issue.Issue) -> str:
    """Prepare markdown content with metadata.
    
    Args:
        issue: GitHub issue object
        
    Returns:
        Formatted markdown content
    """
    body = issue.body or "*No content*"
    
    if INCLUDE_FRONT_MATTER:
        # Add front matter for better blog integration
        front_matter = [
            "---",
            f"title: {issue.title}",
            f"date: {issue.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"author: {issue.user.login}",
            f"issue_number: {issue.number}",
            f"labels: {', '.join(label.name for label in issue.labels)}",
            "---",
            ""
        ]
        return "\n".join(front_matter) + body
    
    return body


def validate_arguments() -> tuple:
    """Validate and parse command line arguments.
    
    Returns:
        Tuple of (token, repo_name, output_path)
        
    Raises:
        SystemExit: If arguments are invalid
    """
    if len(sys.argv) != 4:
        logger.error("Invalid number of arguments")
        print("Usage: python trans_issue_to_md_file.py <token> <repo> <path>")
        sys.exit(1)
    
    token = sys.argv[1]
    repo_name = sys.argv[2]
    output_path = sys.argv[3]
    
    if not token:
        logger.error("GitHub token is required")
        sys.exit(1)
    
    if '/' not in repo_name:
        logger.error(f"Invalid repository name format: {repo_name}")
        logger.error("Expected format: owner/repository")
        sys.exit(1)
    
    return token, repo_name, output_path


@logger.catch
def main() -> None:
    """Main function to process GitHub issues to markdown files."""
    # Parse and validate arguments
    token, repo_name, output_path = validate_arguments()
    
    # Initialize GitHub client
    client = get_github_client(token)
    
    # Get repository
    repo = get_repository(client, repo_name)
    
    # Get publishable issues
    issues = get_publishable_issues(repo)
    
    if not issues:
        logger.info("No issues to process")
        return
    
    # Limit number of issues if configured
    if MAX_ISSUES_TO_PROCESS:
        issues = issues[:MAX_ISSUES_TO_PROCESS]
        logger.info(f"Processing limited to {MAX_ISSUES_TO_PROCESS} issues")
    
    # Process issues
    processed_count = process_issues(issues, output_path)
    
    logger.info(f"Processing complete: {processed_count} issues converted to markdown")


if __name__ == "__main__":
    main()

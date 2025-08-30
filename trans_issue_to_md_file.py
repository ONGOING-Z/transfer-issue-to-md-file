"""
Used for create blog by github repo issues.
"""
# -*- coding: utf-8 -*-

import sys
import time
import os
from pathlib import Path
from typing import List, Optional

from github import Github, GithubException
from loguru import logger


def get_github_user(my_token: str, username: str) -> Optional[object]:
    """
    获得用户
    :param my_token: GitHub access token
    :param username: GitHub username
    :return: GitHub user object or None if failed
    """
    try:
        g = Github(my_token)
        user = g.get_user(str(username))
        logger.info("Successfully accessed GitHub repo.")
        return user
    except GithubException.BadCredentialsException:
        logger.error("GitHub access token has been expired! Please update.")
        return None
    except GithubException.UnknownObjectException:
        logger.error(f"User '{username}' not found.")
        return None
    except Exception as e:
        logger.error(f"Failed to get GitHub user: {e}")
        return None


def get_github_repo(user, repo_name: str) -> Optional[object]:
    """
    获得用户的公开仓库
    :param user: GitHub user object
    :param repo_name: Repository name
    :return: Repository object or None if failed
    """
    try:
        repo = user.get_repo(repo_name)
        logger.info(f"Successfully accessed repository: {repo_name}")
        return repo
    except GithubException.UnknownObjectException:
        logger.error(f"Repository '{repo_name}' not found.")
        return None
    except Exception as e:
        logger.error(f"Failed to get repository: {e}")
        return None


def get_repository_issues(repo) -> Optional[object]:
    """
    获取对应仓库的 issues
    :param repo: Repository object
    :return: Issues paginated list or None if failed
    """
    try:
        # Filter issues by labels for better performance - only get issues with 'blog' label
        issues = repo.get_issues(state='open', labels=['blog'])
        logger.info("Successfully retrieved repository issues with 'blog' label.")
        return issues
    except Exception as e:
        logger.error(f"Failed to get repository issues: {e}")
        return None


def process_issues(issues, blog_path: str) -> int:
    """
    处理标签为 "blog" 和 "need_published" 的 issues
    :param issues: Issues paginated list
    :param blog_path: Path to save markdown files
    :return: Number of processed issues
    """
    if issues is None:
        logger.error("No issues to process.")
        return 0

    issue_num = 0
    res_num = 0
    res_issues_list = []
    
    try:
        for issue in issues:
            issue_num += 1
            if not issue.labels:
                continue
                
            labels_list = get_labels_list(issue.labels)
            # Since we already filtered by 'blog' label, just check for 'need_published'
            if "need_published" in labels_list:
                res_num += 1
                res_issues_list.append(issue.title)
                if write_issue_to_md_file(issue, blog_path):
                    logger.info(f"Successfully processed issue: {issue.title}")
                else:
                    logger.error(f"Failed to process issue: {issue.title}")
                    
    except Exception as e:
        logger.error(f"Error processing issues: {e}")
        return res_num
        
    logger.info(f"Total issues: {issue_num} | Issues to be published: {res_num}")
    if res_num > 0:
        logger.debug(f"Processed issues: {res_issues_list}")
    
    return res_num


def get_labels_list(labels) -> List[str]:
    """
    获取 issue 的 label 列表
    :param labels: GitHub issue labels
    :return: List of label names
    """
    return [label.name for label in labels]


def write_issue_to_md_file(issue, blog_path: str) -> bool:
    """
    将 issue 中的内容写到 markdown 文件中
    :param issue: GitHub issue object
    :param blog_path: Path to save markdown files
    :return: True if successful, False otherwise
    """
    try:
        local_date = time.strftime("%Y-%m-%d", time.localtime())
        body = issue.body or ""  # Handle None body
        
        # Sanitize filename by removing invalid characters
        safe_title = "".join(c for c in issue.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '-')
        
        filename = f"{local_date}-{safe_title}.md"
        
        # Use pathlib for better path handling
        blog_dir = Path(blog_path)
        blog_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = blog_dir / filename
        
        return write_markdown_file(file_path, body, issue.title, issue.html_url, local_date)
        
    except Exception as e:
        logger.error(f"Failed to write issue to markdown file: {e}")
        return False


def write_markdown_file(file_path: Path, body: str, title: str, url: str, date: str) -> bool:
    """
    写文件工具函数
    :param file_path: 文件路径
    :param body: 文件内容
    :param title: issue 标题
    :param url: issue URL
    :param date: 创建日期
    :return: True if successful, False otherwise
    """
    try:
        # Create markdown content with frontmatter
        markdown_content = f"""---
title: "{title}"
date: {date}
source: {url}
tags: [blog]
---

{body}
"""
        
        with open(file_path, "w", encoding="utf-8") as fo:
            fo.write(markdown_content)
        
        logger.info(f"Issue '{title}' content written to {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write markdown file: {e}")
        return False


@logger.catch
def main() -> None:
    """
    主函数
    :return: none
    """
    if len(sys.argv) != 4:
        logger.error("Usage: python script.py <token> <user/repo> <blog_path>")
        sys.exit(1)
        
    my_token = sys.argv[1]
    user_and_repo_name = sys.argv[2]
    blog_path = sys.argv[3]
    
    # Validate input parameters
    if not my_token or not user_and_repo_name or not blog_path:
        logger.error("All parameters are required and cannot be empty.")
        sys.exit(1)
    
    # Parse repository information
    try:
        username, repo_name = user_and_repo_name.split('/', 1)
    except ValueError:
        logger.error("Repository format should be 'username/repository'")
        sys.exit(1)
    
    # Get GitHub user
    user = get_github_user(my_token, username)
    if user is None:
        logger.error("Failed to get GitHub user. Exiting.")
        sys.exit(1)
    
    # Get repository
    repo = get_github_repo(user, repo_name)
    if repo is None:
        logger.error("Failed to get repository. Exiting.")
        sys.exit(1)
    
    # Get repository issues
    issues = get_repository_issues(repo)
    if issues is None:
        logger.error("Failed to get repository issues. Exiting.")
        sys.exit(1)
    
    # Process issues
    processed_count = process_issues(issues, blog_path)
    
    if processed_count > 0:
        logger.info(f"Successfully processed {processed_count} issues.")
    else:
        logger.info("No issues found with 'blog' and 'need_published' labels.")
    
    logger.info("Script execution completed.")


if __name__ == "__main__":
    main()

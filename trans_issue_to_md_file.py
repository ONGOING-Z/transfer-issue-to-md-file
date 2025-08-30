"""
Used for creating blog posts from GitHub repository issues.
"""

import argparse
import os
import re
import sys
import time
from typing import Iterable, List, Optional

from github import Github, GithubException
from loguru import logger


def z_get_user(access_token: str, username: str):
    """
    获取用户
    :param access_token: 访问令牌
    :param username: 用户名
    :return: User 对象
    """
    try:
        github_client = Github(access_token)
        user = github_client.get_user(str(username))
        logger.info("Access to GitHub user succeeded.")
        return user
    except GithubException as exc:
        logger.error(f"Failed to access GitHub user: {exc}")
        return None


def z_get_repo(user, repo_name: str):
    """
    获得用户的仓库
    :param user: User 对象
    :param repo_name: 仓库名
    :return: Repo 对象
    """
    try:
        repo = user.get_repo(repo_name)
        return repo
    except GithubException as exc:
        logger.error(f"Failed to access repository '{repo_name}': {exc}")
        return None


def z_get_issues(repo) -> Iterable:
    """
    获取对应仓库的 issues（包含已关闭，排除 PR）
    :param repo: 仓库
    :return: issues 迭代器
    """
    try:
        issues = repo.get_issues(state="open")
        return issues
    except GithubException as exc:
        logger.error(f"Failed to fetch issues: {exc}")
        return []


def get_labels_list(labels) -> List[str]:
    """
    获取 issue 的 label 名称列表（小写）
    :param labels:
    :return: 标签名称列表
    """
    labels_list: List[str] = []
    for label in labels:
        labels_list.append(label.name.lower())
    return labels_list


def slugify_title(title: str) -> str:
    """
    生成文件名安全的 slug，尽量保留中英文与数字，替换空格为 '-'
    并去除特殊字符，压缩连续的 '-'
    """
    # Normalize whitespace
    title = title.strip()
    # Replace whitespace (including full-width) with '-'
    title = re.sub(r"\s+", "-", title)
    # Remove characters that are not word chars, CJK, hyphen or underscore
    allowed_pattern = re.compile(r"[^\w\-\u4e00-\u9fff]+", re.UNICODE)
    title = allowed_pattern.sub("", title)
    # Collapse multiple dashes
    title = re.sub(r"-+", "-", title)
    # Trim leading/trailing '-'
    title = title.strip("-")
    # Fallback when empty
    if not title:
        title = "post"
    # Limit length to avoid extremely long filenames
    if len(title) > 80:
        title = title[:80].rstrip("-")
    return title


def ensure_directory(path: str) -> None:
    if not path:
        return
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to ensure directory '{path}': {exc}")


def compose_markdown_content(issue, username: str) -> str:
    """
    生成包含 YAML Front Matter 的 Markdown 内容
    """
    labels_raw = get_labels_list(issue.labels)
    # Remove control labels from front matter but keep others
    labels_for_front_matter = [
        label for label in labels_raw if label not in {"blog", "need_published"}
    ]
    local_date = time.strftime("%Y-%m-%d", time.localtime())
    body = issue.body or ""
    # Safely quote YAML scalars
    title_yaml = (issue.title or "").replace("\"", "\\\"")
    labels_serialized = ", ".join([f'"{l.replace("\"", "\\\"")}"' for l in labels_for_front_matter]) if labels_for_front_matter else ""

    front_matter_lines = [
        "---",
        f"title: \"{title_yaml}\"",
        f"date: {local_date}",
        f"labels: [{labels_serialized}]" if labels_for_front_matter else "labels: []",
        f"issue_number: {issue.number}",
        f"issue_url: {issue.html_url}",
        f"author: {username}",
        "---",
        "",
    ]
    return "\n".join(front_matter_lines) + body


def write_issue_to_md_file(issue, output_dir: str, username: str) -> Optional[str]:
    """
    将 issue 中的内容写到 markdown 文件中，并返回写入的文件路径
    """
    ensure_directory(output_dir)
    local_date = time.strftime("%Y-%m-%d", time.localtime())
    file_stem = f"{local_date}-{slugify_title(issue.title)}"
    file_path = os.path.join(output_dir, f"{file_stem}.md")

    # Avoid overwriting: append issue number if the file already exists
    if os.path.exists(file_path):
        file_path = os.path.join(output_dir, f"{file_stem}-{issue.number}.md")

    content = compose_markdown_content(issue, username)
    try:
        with open(file_path, "w", encoding="utf-8", newline="\n") as file_obj:
            file_obj.write(content)
        logger.info(f"<issue: {issue.title}> 内容已写入文件 {file_path} 中!")
        return file_path
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to write markdown file '{file_path}': {exc}")
        return None


def process_issues(issues: Iterable, output_dir: str, username: str) -> None:
    """
    处理标签为 "blog" 和 "need_published" 的 issues
    """
    total_issues = 0
    matched_issues = 0
    published_titles: List[str] = []

    for issue in issues:
        # Skip PRs
        if getattr(issue, "pull_request", None) is not None:
            continue

        total_issues += 1
        if len(issue.labels) == 0:
            continue

        labels_list = get_labels_list(issue.labels)
        if ("blog" in labels_list) and ("need_published" in labels_list):
            if write_issue_to_md_file(issue, output_dir, username):
                matched_issues += 1
                published_titles.append(issue.title)

    logger.info(
        f"Issue amount is {total_issues}. | The issue to be published amount is {matched_issues}."
    )
    if matched_issues != 0:
        logger.debug(published_titles)


def parse_args(argv: List[str]) -> argparse.Namespace:
    """支持新旧两种调用方式：
    1) 兼容旧方式：python script.py <token> <owner/repo> <path>
    2) 新方式：python script.py --token <token> --repo <owner/repo> --path <path>
    若未提供 --token，将回退到环境变量 GITHUB_TOKEN
    """
    # Backward compatibility: positional args
    if len(argv) >= 4 and not argv[1].startswith("-"):
        namespace = argparse.Namespace()
        namespace.token = argv[1]
        namespace.repo = argv[2]
        namespace.path = argv[3]
        return namespace

    parser = argparse.ArgumentParser(description="Transfer GitHub issues to Markdown files")
    parser.add_argument("--token", dest="token", default=os.getenv("GITHUB_TOKEN"), help="GitHub access token (falls back to GITHUB_TOKEN env variable)")
    parser.add_argument("--repo", required=True, help="Repository in the form 'owner/name'")
    parser.add_argument("--path", dest="path", required=True, help="Directory to write generated markdown files")
    return parser.parse_args(argv[1:])


@logger.catch
def main() -> None:
    args = parse_args(sys.argv)

    if not args.token:
        logger.error("GitHub token is required. Provide --token or set GITHUB_TOKEN.")
        sys.exit(1)

    if "/" not in args.repo:
        logger.error("--repo must be in the form 'owner/name'.")
        sys.exit(1)

    username, repo_name = args.repo.split("/", 1)

    user = z_get_user(args.token, username)
    if user is None:
        sys.exit(1)

    repo = z_get_repo(user, repo_name)
    if repo is None:
        sys.exit(1)

    issues = z_get_issues(repo)
    process_issues(issues, args.path, username)


if __name__ == "__main__":
    main()

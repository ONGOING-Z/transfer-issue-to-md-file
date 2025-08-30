"""
Used for creating blog posts from GitHub repository issues.
"""
# -*- coding: utf-8 -*-

import re
import sys
import time
from pathlib import Path
from typing import List

from github import Github, GithubException
from loguru import logger


def z_get_user(my_token: str, username: str):
    """
    获得用户
    :param my_token:
    :param username
    :return:
    """
    g = Github(my_token)
    try:
        user = g.get_user(str(username))
    except GithubException as exc:
        logger.error(f"Failed to access GitHub user '{username}': {exc}")
        raise
    else:
        logger.info("Accessed GitHub user successfully.")
        return user


def z_get_repo(user, repo_name: str):
    """
    获得用户的公开仓库
    :param user
    :param repo_name
    :return: repo
    """
    try:
        repo = user.get_repo(repo_name)
    except GithubException as exc:
        logger.error(f"Failed to access repository '{repo_name}': {exc}")
        raise
    else:
        return repo


def z_get_issues(repo):
    """
    获取对应仓库的 issues
    :param repo: 仓库
    :return: issues
    """
    # Default to open issues; adjust if needed
    issues = repo.get_issues(state="open")
    return issues


def process_issues(issues, output_dir: Path) -> None:
    """
    处理标签为 "blog" 和 "need_published" 的 issues
    :param issues:
    :return: none
    """

    issue_num = 0
    res_num = 0
    res_issues_list: List[str] = []
    for issue in issues:
        issue_num = issue_num + 1  # compute all issues number
        if len(issue.labels) != 0:
            labels = issue.labels
            labels_list = get_labels_list(labels)
            # issue 标签中有 blog 和 need_published 的才会发布
            if ("blog" in labels_list) and ("need_published" in labels_list):
                res_num = res_num + 1  # compute the issues number by conditions
                res_issues_list.append(issue.title)
                write_issue_to_md_file(issue, output_dir)
            else:
                continue
    logger.info(
        f"Issue amount is {issue_num}. | The issue to be published amount is {res_num}."
    )
    if res_num != 0:
        logger.debug(res_issues_list)


def get_labels_list(labels) -> List[str]:
    """
    获取 issue 的 label 列表
    :param labels:
    :return:
    """
    return [label.name for label in labels]


def write_issue_to_md_file(issue, output_dir: Path) -> None:
    """
    将 issue 中的内容写到 markdown 文件中
    :param issue:
    :return: none
    """
    local_date = time.strftime("%Y-%m-%d", time.localtime())
    body = issue.body or ""
    safe_title = sanitize_filename(issue.title)
    # the generated markdown file's name should be like '2021-08-09-xxx.md'
    name = f"{local_date}-{safe_title}"
    output_dir.mkdir(parents=True, exist_ok=True)
    io_util(output_dir / name, body, issue.title)


def io_util(file_path: Path, file_body: str, issue_title: str) -> None:
    """
    写文件工具函数
    :param issue_title: issue 名称
    :param file_path: 文件路径（不带扩展名）
    :param file_body: 文件内容
    :return:
    """
    try:
        with open(file_path.with_suffix(".md"), "w", encoding="utf-8", newline="\n") as file_obj:
            file_obj.write(file_body)
        logger.info(f"<issue: {issue_title}> 内容已写入文件{file_path.name}.md 中!")
    except OSError as exc:
        logger.error(f"写入文件失败: {file_path.with_suffix('.md')}. 错误: {exc}")
        raise


def sanitize_filename(title: str) -> str:
    """
    Sanitize a string to be a safe filename while preserving non-ASCII characters
    (e.g., Chinese). Replaces path separators and reserved characters with '-'.
    """
    if title is None:
        return "untitled"
    # Collapse whitespace to single spaces
    value = re.sub(r"\s+", " ", str(title)).strip()
    # Replace reserved characters (across common filesystems) with '-'
    value = re.sub(r"[<>:\\/\|\?\*]", "-", value)
    # Replace remaining spaces with '-'
    value = re.sub(r"\s", "-", value)
    # Collapse multiple dashes
    value = re.sub(r"-+", "-", value)
    # Trim leading/trailing dashes
    return value.strip("-") or "untitled"


@logger.catch
def main() -> None:
    """
    主函数
    :return: none
    """
    if len(sys.argv) < 4:
        logger.error("Usage: trans_issue_to_md_file.py <token> <owner/repo> <output_dir>")
        sys.exit(1)

    my_token = sys.argv[1]
    # Get current repository name
    user_and_repo_name = sys.argv[2]
    try:
        username, repo_name = user_and_repo_name.split("/", 1)
    except ValueError:
        logger.error("Repository must be in the format 'owner/repo'.")
        sys.exit(1)
    output_dir = Path(sys.argv[3])
    # 获取用户
    user = z_get_user(my_token, username)
    # 根据仓库名和用户获取对应仓库
    if user is not None:
        repo = z_get_repo(user, repo_name)
    # 根据仓库获取仓库的 issue
    issues = z_get_issues(repo)
    # 对符合条件的 issue 进行处理
    process_issues(issues, output_dir)


if __name__ == "__main__":
    main()

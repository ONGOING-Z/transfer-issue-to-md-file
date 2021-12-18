"""
Used for create blog by github repo issues.
"""
# todo: 题目
# 中文和英文之间的空格消除
# 英文和英文之间的空格用 ‘-’ 代替
# -*- coding: utf-8 -*-

import sys
import time

from github import Github, GithubException
from loguru import logger

blog_path = sys.argv[3]


def z_get_user(my_token, username):
    """
    获得用户
    :param my_token:
    :param username
    :return:
    """
    try:
        g = Github(my_token)
    except GithubException.BadCredentialsException:
        logger.error("github access token has been expired! Please update.")
    else:
        logger.info("access github repo done.")

    user = g.get_user(str(username))
    return user


def z_get_repo(user, repo_name):
    """
    获得用户的公开仓库
    :param user
    :param repo_name
    :return: repo
    """
    repo = user.get_repo(repo_name)
    return repo


def z_get_issues(repo):
    """
    获取对应仓库的 issues
    :param repo: 仓库
    :return: issues
    """
    issues = repo.get_issues()
    return issues


def process_issues(issues):
    """
    处理标签为 "blog" 和 "need_published" 的 issues
    :param issues:
    :return: none
    """

    issue_num = 0
    res_num = 0
    res_issues_list = []
    for issue in issues:
        issue_num = issue_num + 1  # compute all issues number
        if len(issue.labels) != 0:
            labels = issue.labels
            labels_list = get_labels_list(labels)
            # issue 标签中有 blog 和 need_published 的才会发布
            if ("blog" in labels_list) and ("need_published" in labels_list):
                res_num = res_num + 1  # compute the issues number by conditions
                res_issues_list.append(issue.title)
                write_issue_to_md_file(issue)
            else:
                continue
    logger.info(
        f"Issue amount is {issue_num}. | The issue to be published amount is {res_num}."
    )
    if res_num != 0:
        logger.debug(res_issues_list)


def get_labels_list(labels):
    """
    获取 issue 的 label 列表
    :param labels:
    :return:
    """
    labels_list = []
    for label in labels:
        labels_list.append(label.name)
    return labels_list


def write_issue_to_md_file(issue) -> None:
    """
    将 issue 中的内容写到 markdown 文件中
    :param issue:
    :return: none
    """
    global blog_path
    local_date = time.strftime("%Y-%m-%d", time.localtime())
    body = issue.body
    name = (
        local_date + "-" + issue.title
    )  # the generated markdown file's name should be like '2021-08-09-xxx.md'
    if blog_path[len(blog_path) - 1] == '/':
        pass
    else:
        blog_path = blog_path + '/'
    new_name = blog_path + name
    io_util(new_name, body, issue.title)


def io_util(file_name, file_body, issue_title) -> None:
    """
    写文件工具函数
    :param issue_title: issue 名称
    :param file_name: 文件名称
    :param file_body: 文件内容
    :return:
    """
    fo = open(f"{file_name}.md", "w+")
    fo.write(file_body)

    logger.info(f"<issue: {issue_title}> 内容已写入文件{file_name}.md中!")


@logger.catch
def main() -> None:
    """
    主函数
    :return: none
    """
    my_token = sys.argv[1]
    # Get current repostory name
    user_and_repo_name = sys.argv[2]
    results = user_and_repo_name.split('/')
    username = results[0]
    repo_name = results[1]
    # 获取用户
    user = z_get_user(my_token, username)
    # 根据仓库名和用户获取对应仓库
    if user is not None:
        repo = z_get_repo(user, repo_name)
    # 根据仓库获取仓库的 issue
    issues = z_get_issues(repo)
    # 对符合条件的 issue 进行处理
    process_issues(issues)


if __name__ == "__main__":
    main()

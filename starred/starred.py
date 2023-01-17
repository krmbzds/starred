#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from io import BytesIO
from collections import OrderedDict
import click
from github3 import GitHub
from github3.exceptions import NotFoundError
from . import VERSION
from .githubgql import GitHubGQL


DEFAULT_CATEGORY = 'Others'
TEXT_LENGTH_LIMIT = 200

desc = '''
= Stars
Kerem Bozdas
:idprefix:
:idseparator: -
:page-pagination:
:description: A curated list of my GitHub stars.
'''

html_escape_table = {
    ">": "&gt;",
    "<": "&lt;",
}


def html_escape(text):
    """Produce entities within text."""
    return "".join(html_escape_table.get(c, c) for c in text)


@click.command()
@click.option('--username', envvar='USER', required=True, help='GitHub username')
@click.option('--token', envvar='GITHUB_TOKEN', required=True, help='GitHub token')
@click.option('--sort',  is_flag=True, show_default=True, help='sort by category[language/topic] name alphabetically')
@click.option('--topic', is_flag=True, show_default=True, help='category by topic, default is category by language')
@click.option('--topic_limit', default=500, show_default=True, type=int, help='topic stargazer_count gt number, set bigger to reduce topics number')
@click.option('--repository', default='', show_default=True, help='repository name')
@click.option('--filename', default='modules/ROOT/pages/stars.adoc', show_default=True, help='file name')
@click.option('--message', default='Update starred repos', show_default=True, help='commit message')
@click.option('--private', is_flag=True, default=False, show_default=True, help='include private repos')
@click.version_option(version=VERSION, prog_name='starred')
def starred(username, token, sort, topic, repository, filename, message, private, topic_limit):
    """GitHub starred

    creating your own Awesome List by GitHub stars!

    example:
        starred --username krmbzds --token=xxxxxxxx --sort > README.md
    """

    gh = GitHubGQL(token)
    try:
        stars = gh.get_user_starred_by_username(username, topic_stargazer_count_limit=topic_limit)
    except Exception as e:
        click.secho(f'Error: {e}', fg='red')
        return

    if repository:
        file = BytesIO()
        sys.stdout = file
    else:
        file = None

    click.echo(desc)
    repo_dict = {}

    for s in stars:
        # skip private repos if --private is not set
        if s.is_private and not private:
            continue

        description = html_escape(s.description).replace('\n', '').strip()[:TEXT_LENGTH_LIMIT] if s.description else ''

        if topic:
            for category in s.topics or [DEFAULT_CATEGORY.lower()]:
                if category not in repo_dict:
                    repo_dict[category] = []
                repo_dict[category].append([s.name, s.url, description])
        else:
            category = s.language or DEFAULT_CATEGORY

            if category not in repo_dict:
                repo_dict[category] = []
            repo_dict[category].append([s.url, s.name, description])

    if sort:
        repo_dict = OrderedDict(sorted(repo_dict.items(), key=lambda cate: cate[0]))

    for category in repo_dict:
        click.echo('== {} \n'.format(category.replace('#', '# #')))
        for repo in repo_dict[category]:
            data = u'* {}[{}] - {}'.format(*repo)
            click.echo(data)
        click.echo('')

    if file:
        gh = GitHub(token=token)
        try:
            rep = gh.repository(username, repository)
            try:
                rep.file_contents(f'/{filename}').update(message, file.getvalue())
            except NotFoundError:
                rep.create_file(filename, message, file.getvalue())
        except NotFoundError:
            pass

if __name__ == '__main__':
    starred()

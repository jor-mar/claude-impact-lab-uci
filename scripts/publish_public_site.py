#!/usr/bin/env python3
"""Publish the committed dist/ snapshot to the existing public hosting repository."""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOSTING_REMOTE = 'https://github.com/LoganWu123/fund-it.git'
PUBLIC_URL = 'https://loganwu123.github.io/fund-it/'


def git(*args, env=None, input=None):
    result = subprocess.run(['git', *args], cwd=ROOT, env=env, input=input,
                            text=True, capture_output=True, check=True)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true', help='Push the committed website; default only shows the plan')
    args = parser.parse_args()
    source = git('rev-parse', 'HEAD')
    git('rev-parse', source + ':dist')
    print(f'Source commit: {source}\nHosting repository: {HOSTING_REMOTE}\nPublic URL: {PUBLIC_URL}')
    if not args.publish:
        print('Preview only. Add --publish to deploy the committed dist/ snapshot.')
        return
    with tempfile.TemporaryDirectory(prefix='fundit-publish-') as folder:
        env = {**os.environ, 'GIT_INDEX_FILE': str(Path(folder) / 'index'), 'GIT_TERMINAL_PROMPT': '0'}
        git('fetch', '--no-tags', HOSTING_REMOTE, 'gh-pages', env=env)
        parent = git('rev-parse', 'FETCH_HEAD', env=env)
        git('read-tree', source + ':dist', env=env)
        empty_blob = git('hash-object', '-w', '--stdin', env=env, input='')
        git('update-index', '--add', '--cacheinfo', f'100644,{empty_blob},.nojekyll', env=env)
        tree = git('write-tree', env=env)
        if tree == git('rev-parse', parent + '^{tree}', env=env):
            print('The public hosting branch already has these website files.')
            return
        commit = git('commit-tree', tree, '-p', parent, '-m', f'Publish Fund it from source {source[:7]}', env=env)
        # Fast-forward push rejects concurrent changes; never force a deployment.
        git('push', HOSTING_REMOTE, commit + ':refs/heads/gh-pages', env=env)
        print(f'Uploaded website commit {commit}. GitHub Pages will build it; verify {PUBLIC_URL} before sharing an update.')


if __name__ == '__main__':
    main()

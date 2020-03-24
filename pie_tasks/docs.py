from pathlib import Path

from pie import *

ROOT_DIR = Path('.').absolute()
DOCS_DIR = ROOT_DIR/'docs'


def docker_run(c):
    cmd(r'docker run --rm -it -v "{}:/app" intergov_docs/build {}'.format(ROOT_DIR, c))


@task
def build_docker_image():
    with cd(DOCS_DIR):
        cmd(r'docker image build -t intergov_docs/build --rm docker')


@task
def build_docs():
    sphinx_args = [
        '-a',
        '-v',
        '-b html',
        'docs',
        'docs/_build/html',
    ]
    with cd(DOCS_DIR):
        docker_run('python -m sphinx {}'.format(' '.join(sphinx_args)))


@task
def sphinx_help():
    with cd(DOCS_DIR):
        docker_run('python -m sphinx --help')


@task
def bash():
    with cd(DOCS_DIR):
        docker_run('/bin/bash')

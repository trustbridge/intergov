from pathlib import Path

from pie import *
from pie_docker import *


ROOT_DIR = Path('.').absolute()
DOCS_BUILDER_IMAGE_NAME='igl__intergov/docs_builder'


def _run_docs_builder(c,listen_port=False):
    run_options=['--rm','-it',f'-v "{ROOT_DIR}:/app"','--name igl__shared_db_channel__docs_builder']
    if listen_port:
        run_options.append('-p 8990:80')
    Docker().run(DOCS_BUILDER_IMAGE_NAME,c,run_options)


@task
def create_docker_image():
    """Create the docker image that can build the docs"""
    Docker().build('.',['-f docs/docker/Dockerfile',f'-t {DOCS_BUILDER_IMAGE_NAME}','--no-cache','--rm'])


@task
def build_docs():
    """Build the docs and exit"""
    sphinx_args = [
        '-a',
        '-v',
        '-b html',
        'docs',
        'docs/_build/html',
    ]
    _run_docs_builder('sphinx-apidoc -o docs/_modules intergov')
    _run_docs_builder('python -m sphinx {}'.format(' '.join(sphinx_args)))


@task
def build_docs_autobuild():
    """Build the docs and run a server that hosts the docs and will automatically rebuild them on changes"""
    sphinx_args = [
        '-a',
        '-v',
        '-b html',
        '-p 80',
        '-H 0.0.0.0',
        '--ignore docs/_build/*',
        'docs',
        'docs/_build/html',
    ]
    _run_docs_builder('sphinx-autobuild {}'.format(' '.join(sphinx_args)),listen_port=True)


@task
def sphinx_help():
    """Get sphinx help"""
    _run_docs_builder('python -m sphinx --help')


@task
def bash():
    """Bash terminal within the doc builder container"""
    _run_docs_builder('bash')

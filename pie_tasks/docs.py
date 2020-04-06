from pathlib import Path

from pie import *
from pie_docker import *


ROOT_DIR = Path('.').absolute()
DOCS_DIR = ROOT_DIR/'docs'


def _run_docs_container(c,listen_port=False):
    run_options=['--rm','-it','-v "{}:/app"'.format(ROOT_DIR)]
    if listen_port:
        run_options.append('-p 8998:8998')
    Docker().run('intergov_docs/build',c,run_options)


@task
def create_docker_image():
    """Create the docker image that can build the docs"""
    with cd(DOCS_DIR):
        Docker().build('docker',['--no-cache','-t intergov_docs/build','--rm'])


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
    with cd(DOCS_DIR):
        _run_docs_container('python -m sphinx {}'.format(' '.join(sphinx_args)))


@task
def build_docs_autobuild():
    """Build the docs and run a server that hosts the docs and will automatically rebuild them on changes"""
    sphinx_args = [
        '-a',
        '-v',
        '-b html',
        '-p 8998',
        '-H 0.0.0.0',
        '--ignore docs/_build/*',
        'docs',
        'docs/_build/html',
    ]
    with cd(DOCS_DIR):
        _run_docs_container('sphinx-autobuild {}'.format(' '.join(sphinx_args)),listen_port=True)


@task
def sphinx_help():
    """Get sphinx help"""
    with cd(DOCS_DIR):
        _run_docs_container('python -m sphinx --help')


@task
def bash():
    """Bash terminal within the doc builder container"""
    with cd(DOCS_DIR):
        _run_docs_container('bash')
